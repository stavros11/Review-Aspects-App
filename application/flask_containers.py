import os
import json
import flask
from application import directories
from aspects import containers

import plotly
from plotly import graph_objects as go

from typing import Optional, Tuple


class Aspect:

  def __init__(self, word: str, hotel_id: str,
               container: containers.AspectContainers):
    self.text = word
    self.hotel_id = hotel_id
    self.container = container

  @property
  def pos_score(self) -> float:
    return self.container.pos_scores[self.text]

  @property
  def neg_score(self) -> float:
    return self.container.neg_scores[self.text]

  @property
  def pos_appearances(self) -> int:
    return self.container.pos_appearances[self.text]

  @property
  def neg_appearances(self) -> int:
    return self.container.neg_appearances[self.text]

  @property
  def url(self) -> str:
    return flask.url_for("main", hotelname=self.hotel_id, word=self.text)


class Hotel:

  def __init__(self, folder_name: str, pkl_name: Optional[str] = None):
    self.id = folder_name
    if pkl_name is None:
      self.pkl_name = directories.hotel_db[folder_name]
    else:
      self.pkl_name = pkl_name

    self.hotel_dir = os.path.join(directories.trip_advisor, self.id)
    with open(self.find_txt(self.hotel_dir), "r") as file:
      hotel_data = json.load(file)
    for k, v in hotel_data.items():
      setattr(self, k, v)

    self.aspects = containers.DataAspects.load(
        os.path.join(self.hotel_dir, self.pkl_name))

  @staticmethod
  def find_txt(data_dir: str):
    all_files = os.listdir(data_dir)
    txt = None
    for file in all_files:
      if file.split(".")[-1] == "txt":
        if txt is None:
          txt = file
        else:
          raise ValueError("Multiple .txt files found in {}.".format(data_dir))
    if txt is None:
      raise ValueError("Could not find .txt file in {}.".format(data_dir))
    return os.path.join(data_dir, txt)

  @property
  def app_url(self):
    return flask.url_for("main", hotelname=self.id)

  @property
  def n_reviews(self) -> int:
    return sum(self.ratingCounts)

  @property
  def n_reviews_aspects_sentiment(self) -> Tuple[int, int, int]:
    aspects_series = self.aspects.aspects_per_review
    pos, neutral, neg = 0, 0, 0
    for aspect_counter in aspects_series:
      total_sentiment = sum(aspect_counter.values())
      if total_sentiment > 0:
        pos += 1
      elif total_sentiment < 0:
        neg += 1
      else:
        neutral = 0
    return neg, neutral, pos

  @property
  def n_reviews_hasnegative(self) -> Tuple[int, int]:
    sentiment = self.aspects.has_negative
    neg = (sentiment == "Negative").sum()
    pos = (sentiment == "Positive").sum()
    neutral = (sentiment == "N/A").sum()
    return neg, neutral, pos

  @staticmethod
  def encode_plot(plot):
    return json.dumps([plot], cls=plotly.utils.PlotlyJSONEncoder)

  @property
  def rating_counts_barchart(self):
    # orientation='h' for horizontal bars
    n = len(self.ratingCounts)
    bar = go.Bar(x=list(range(1, n + 1)), y=self.ratingCounts)
    return self.encode_plot(bar)

  _PIE_COLORS = ["rgb(227,26,28)", "rgb(251,154,153)", "rgb(166,206,227)",
                 "rgb(129,218,85)", "rgb(51,160,44)"]

  @property
  def rating_counts_piechart(self):
    n = len(self.ratingCounts)
    pie = go.Pie(labels=list(range(1, n + 1)), values=self.ratingCounts,
                 marker_colors=self._PIE_COLORS)
    return self.encode_plot(pie)

  @property
  def aspects_sentiment_piechart(self):
    labels = ["Negative", "Neutral", "Positive"]
    colors = [self._PIE_COLORS[0], self._PIE_COLORS[2], self._PIE_COLORS[-1]]
    pie = go.Pie(labels=labels, values=list(self.n_reviews_aspects_sentiment),
                 marker_colors=colors)
    return self.encode_plot(pie)

  @property
  def aspects_hasnegative_piechart(self):
    labels = ["Negative", "Neutral", "Positive"]
    colors = [self._PIE_COLORS[0], self._PIE_COLORS[2], self._PIE_COLORS[-1]]
    pie = go.Pie(labels=labels, values=list(self.n_reviews_hasnegative),
                 marker_colors=colors)
    return self.encode_plot(pie)

  @property
  def additionalrating_radarchart(self):
    categories, ratings = [], []
    for category, rating in self.additionalRatings.items():
      categories.append(category)
      ratings.append(rating)
    radar = go.Scatterpolar(r=ratings, theta=categories, fill='toself')
    return self.encode_plot(radar)

  @property
  def additionalrating_barchart(self):
    categories, ratings = [], []
    for category, rating in self.additionalRatings.items():
      categories.append(category)
      ratings.append(rating)
    radar = go.Bar(y=categories, x=ratings, orientation="h", width=0.3)
    return self.encode_plot(radar)


def aspects_generator(word: str, hotel_id: str,
                      container: containers.AspectContainers,
                      mode: str = "pos_scores", start: int = 0, end: int = 50):
  counter = getattr(container, mode)
  for word, _ in counter.most_common()[start: end]:
    yield Aspect(word, hotel_id, container)