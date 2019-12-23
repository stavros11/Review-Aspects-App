import flask
import pandas as pd
import json
from app import db
from app import stopwords

import plotly
from plotly import graph_objects as go

from typing import Any, Dict, List


class Hotel(db.Model):
  id = db.Column(db.String(128), primary_key=True)
  name = db.Column(db.String(128), unique=True)
  absoluteUrl = db.Column(db.String(512), unique=True)
  imageUrl = db.Column(db.String(1024), unique=True)
  locationId = db.Column(db.Integer)
  accommodationCategory = db.Column(db.String(32))
  reviews = db.relationship("Review", lazy="dynamic")

  ratingCounts_serialized = db.Column(db.String(64))
  languageCounts_serialized = db.Column(db.String(128))
  additionalRatings_serialized = db.Column(db.String(128))

  def __repr__(self):
    return '<Hotel {}>'.format(self.username)

  @property
  def n_reviews(self) -> int:
    return self.reviews.count()

  def get_reviews(self, order_by: str = "publishedDate"):
    order_obj = getattr(Review, order_by)
    return self.reviews.order_by(order_obj.desc())

  @property
  def ratingCounts(self) -> List[int]:
    return json.loads(self.ratingCounts_serialized)

  @property
  def languageCounts(self) -> Dict[str, int]:
    return json.loads(self.languageCounts_serialized)

  @property
  def additionalRatings(self) -> Dict[str, float]:
    return json.loads(self.additionalRatings_serialized)

  @property
  def app_url(self):
    """URL that redirects back to the hotel's main page."""
    return flask.url_for("analysis", hotel_id=self.id)

  @classmethod
  def create(cls, id: str, metadata: Dict[str, Any]) -> "Hotel":
    # If the key `id` is not found in metadata use the folders name
    # The `id` key is required to generate URLs
    if "id" in metadata:
      raise KeyError("Hotel ID found in metadata txt.")

    metadata["id"] = id
    metadata["ratingCounts_serialized"] = json.dumps(
        metadata.pop("ratingCounts"))
    metadata["languageCounts_serialized"] = json.dumps(
        metadata.pop("languageCounts"))
    metadata["additionalRatings_serialized"] = json.dumps(
        metadata.pop("additionalRatings"))

    return cls(**metadata)

  @staticmethod
  def encode_plot(*plot):
    return json.dumps(list(plot), cls=plotly.utils.PlotlyJSONEncoder)

  _PIE_COLORS = ["rgb(227,26,28)", "rgb(251,154,153)", "rgb(166,206,227)",
                 "rgb(129,218,85)", "rgb(51,160,44)"]

  @property
  def rating_counts_piechart(self):
    labels, values = [], []
    for l, v in pd.value_counts(self.ratingCounts).items():
      labels.append(l)
      values.append(v)
    pie = go.Pie(labels=labels, values=values,
                 marker_colors=self._PIE_COLORS[::-1])
    return self.encode_plot(pie)

  @property
  def additionalrating_barchart(self):
    categories, ratings = [], []
    for category, rating in self.additionalRatings.items():
      categories.append(category)
      ratings.append(rating)
    bar = go.Bar(y=categories, x=ratings, orientation="h", width=0.3)
    return self.encode_plot(bar)


class Review(db.Model):
  # Reminder: Can add more columns here
  id = db.Column(db.Integer, primary_key=True)
  absoluteUrl = db.Column(db.String(512), index=True, unique=True)
  createdDate = db.Column(db.String(32))
  stayDate = db.Column(db.String(32))
  publishedDate = db.Column(db.String(32))
  rating = db.Column(db.Float)

  username = db.Column(db.String(256))
  userId = db.Column(db.String(256))
  user_hometownId = db.Column(db.Integer)
  user_hometownName = db.Column(db.String(256))

  title = db.Column(db.String(2048))
  text = db.Column(db.String(100000))
  spacy_text = db.Column(db.String(500000))

  hotelId = db.Column(db.String(128), db.ForeignKey("hotel.id"))

  _VALID_KEYS = {"id", "absoluteUrl", "createdDate", "stayDate",
                 "publishedDate", "rating",
                 "username", "userId", "user_hometownId", "user_hometownName",
                 "title", "text", "spacy_text", "hotelId"}

  @classmethod
  def from_series(cls, data: pd.Series, hotel_id: str):
    args = {k: v for k, v in data.items() if k in cls._VALID_KEYS}
    args["hotelId"] = hotel_id

    if "spacy_text" in args and not isinstance(args["spacy_text"], bytes):
      args["spacy_text"] = args.pop("spacy_text").to_bytes()

    return cls(**args)


sentences = db.Table('tags',
    db.Column('unigram_text', db.String(64), db.ForeignKey('unigram.text'),
              primary_key=True),
    db.Column('sentence_id', db.Integer, db.ForeignKey('sentence.id'),
              primary_key=True))


class Unigram(db.Model):
  text = db.Column(db.String(64), primary_key=True)
  score = db.Column(db.Float)
  sentences = db.relationship("Sentence", secondary=sentences, lazy="subquery",
                              backref=db.backref("unigrams", lazy=True))

  VALID_POS_ = {"NOUN", "PROPN"}

  @classmethod
  def unigrams(cls, doc: "spacy.tokens.Doc"):
    """Creates dict from unigrams to spacy tokens"""
    word_to_sentences = {} # Dict[str, List[spacy.tokens.Span]]
    for token in doc:
      text = token.text.lower()
      if (len(text) > 1 and text not in stopwords.INVALID_TOKENS
          and token.pos_ in cls.VALID_POS_):
        sentence = token.sent
        if text in word_to_sentences:
          if sentence == word_to_sentences[text][-1].sentence:
            word_to_sentences[text][-1].append(token)
          else:
            word_to_sentences[text].append(Sentence(sentence, token, review))
        else:
          word_to_sentences[text] = SentenceCollection(
              text, Sentence(sentence, token, review))
    return cls(word_to_sentences)


class Sentence(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String(10000))
