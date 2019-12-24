import os
import collections
import flask
import pandas as pd
import json
import spacy
from app import app
from app import db
from app import stopwords

import plotly
from plotly import graph_objects as go
from nltk.sentiment import vader
SID = vader.SentimentIntensityAnalyzer()

from typing import Any, Dict, List, Tuple


unigram_sentences = db.Table('sentences',
    db.Column('unigram_text', db.String(128), db.ForeignKey('unigram.text')),
    db.Column('sentence_id', db.String(128), db.ForeignKey('sentence.id')))


class Unigram(db.Model):
  text = db.Column(db.String(128), primary_key=True)
  hotelId = db.Column(db.String(128), db.ForeignKey("hotel.id"))
  sentences = db.relationship("Sentence", secondary=unigram_sentences,
                              lazy='subquery',
                              backref=db.backref("unigrams", lazy=True))

  VALID_UNIGRAM_POS_ = {"NOUN", "PROPN"}

  @property
  def appearances(self) -> int:
    return len(self.sentences)

  @property
  def url(self) -> str:
    return flask.url_for("analysis", hotel_id=self.hotelId, word=self.text)

  @property
  def positive_sentences(self) -> collections.Counter:
    counter = collections.Counter({s: s.score for s in self.sentences
                                   if s.polarity > 0})
    return counter.most_common()

  @property
  def neutral_sentences(self) -> collections.Counter:
    counter = collections.Counter({s: s.score for s in self.sentences
                                   if s.polarity == 0})
    return counter.most_common()

  @property
  def negative_sentences(self) -> collections.Counter:
    counter = collections.Counter({s: -s.score for s in self.sentences
                                   if s.polarity < 0})
    return counter.most_common()


class Sentence(db.Model):
  # id has the format "{reviewId}_{position in review}"
  id = db.Column(db.String(128), primary_key=True)
  position = db.Column(db.Integer)
  reviewId = db.Column(db.Integer, db.ForeignKey("review.id"))
  score = db.Column(db.Float)

  _review = None

  @staticmethod
  def generate_id(reviewId: int, position: int) -> str:
    return "_".join([str(reviewId), str(position)])

  @classmethod
  def create(cls, position: int, reviewId: int, text: str):
    id = cls.generate_id(reviewId, position)
    sentiment = SID.polarity_scores(text)
    score = sentiment["compound"]
    return cls(id=id, position=position, reviewId=reviewId, score=score)

  @property
  def review(self) -> "Review":
    if self._review is not None:
      return self._review
    self._review = Review.query.get(self.reviewId)
    return self._review

  @property
  def text(self) -> str:
    return list(self.review.spacy_text.sents)[self.position].text

  @property
  def polarity(self, cutoff: float = 0.2) -> int:
    if self.score > cutoff:
      return 1
    elif self.score < - cutoff:
      return -1
    else:
      return 0


class Hotel(db.Model):
  id = db.Column(db.String(128), primary_key=True)
  name = db.Column(db.String(128), unique=True)
  absoluteUrl = db.Column(db.String(512), unique=True)
  imageUrl = db.Column(db.String(1024), unique=True)
  locationId = db.Column(db.Integer)
  accommodationCategory = db.Column(db.String(32))
  reviews = db.relationship("Review", lazy="dynamic")
  unigrams = db.relationship("Unigram", lazy="dynamic")

  ratingCounts_serialized = db.Column(db.String(64))
  languageCounts_serialized = db.Column(db.String(128))
  additionalRatings_serialized = db.Column(db.String(128))

  def __repr__(self):
    return '<Hotel {}>'.format(self.id)

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

  @property
  def common_unigrams(self) -> List[Tuple[Unigram, int]]:
    counter = collections.Counter({t: t.appearances for t in self.unigrams})
    return counter.most_common()

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
  spacyText_bytes = db.Column(db.String(500000))

  hotelId = db.Column(db.String(128), db.ForeignKey("hotel.id"))
  sentences = db.relationship("Sentence", lazy="dynamic")

  _spacy_text = None

  VALID_KEYS = {"id", "absoluteUrl", "createdDate", "stayDate",
                 "publishedDate", "rating",
                 "username", "userId", "user_hometownId", "user_hometownName",
                 "title", "text", "spacy_text", "hotelId"}

  def __repr__(self):
    return '<Review {} of Hotel {}>'.format(self.id, self.hotelId)

  @classmethod
  def from_series(cls, data: pd.Series, hotel_id: str):
    args = {k: v for k, v in data.items() if k in cls.VALID_KEYS}
    args["hotelId"] = hotel_id

    if "spacy_text" in args and not isinstance(args["spacy_text"], bytes):
      args["spacyText_bytes"] = args.pop("spacy_text").to_bytes()

    review = cls(**args)
    review._spacy_text = data["spacy_text"]
    return review

  @property
  def spacy_text(self) -> spacy.tokens.Doc:
    if self._spacy_text is not None:
      return self._spacy_text

    vocab_path = os.path.join(app.config["STORAGE_PATH"],
                              "vocab_{}".format(self.hotelId))
    vocab = spacy.vocab.Vocab().from_disk(vocab_path)
    self._spacy_text = spacy.tokens.Doc(vocab).from_bytes(self.spacyText_bytes)
    return self._spacy_text

  def create_sentences(self, unigrams: Dict[str, Unigram]
                       ) -> Tuple[List[Sentence], Dict[str, Unigram]]:
    sentences = []
    for pos, sent in enumerate(self.spacy_text.sents):
      # TODO: Implement score using a sentiment classifier
      sentence = Sentence.create(position=pos, reviewId=self.id, text=sent.text)
      sentences.append(sentence)
      for token in sent:
        text = token.text.lower()
        if (len(text) > 1 and text not in stopwords.INVALID_TOKENS
            and token.pos_ in Unigram.VALID_UNIGRAM_POS_):
          if text not in unigrams:
            unigrams[text] = Unigram(text=text, hotelId=self.hotelId)
          unigrams[text].sentences.append(sentence)
    return sentences, unigrams
