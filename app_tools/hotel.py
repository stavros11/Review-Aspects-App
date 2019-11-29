import os
import json
import flask
import pandas as pd
from app_tools import directories
from aspects import containers

import plotly
from plotly import graph_objects as go

from typing import Any, Dict, Optional, Tuple


class Hotel:

  def __init__(self, id: str,
               aspects: containers.DataAspects,
               hotel_data: Optional[Dict[str, Any]] = None,
               load_name: Optional[str] = None):
    self.id = id
    self.aspects = aspects
    self.load_name = load_name
    for k, v in hotel_data.items():
      setattr(self, k, v)

  @classmethod
  def load_from_local(cls, folder_name: str, pkl_name: Optional[str] = None
                      ) -> "Hotel":
    """Loads a hotel using a file (pickle) from local disk."""
    if pkl_name is None:
      pkl_name = directories.hotel_db[folder_name]
    else:
      pkl_name = pkl_name

    hotel_dir = os.path.join(directories.trip_advisor, folder_name)
    with open(cls.find_txt(hotel_dir), "r") as file:
      hotel_data = json.load(file)

    aspects_dir = os.path.join(hotel_dir, pkl_name)
    aspects = containers.DataAspects.load(aspects_dir)

    return cls(folder_name, aspects, hotel_data, load_name=pkl_name)

  @staticmethod
  def find_txt(data_dir: str):
    """Finds all `txt` files in the given directory.

    Args:
      data_dir: The directory path to search for `txt`.

    Returns:
      The full path of the found `text`.

    Raises:
      FileExistsError if more than one `txt`s are found in the given path.
      FileNotFoundError if no `txt`s exist in the given.
    """
    all_files = os.listdir(data_dir)
    txt = None
    for file in all_files:
      if file.split(".")[-1] == "txt":
        if txt is None:
          txt = file
        else:
          raise FileExistsError("Multiple .txt files found in {}.".format(data_dir))
    if txt is None:
      raise FileNotFoundError("Could not find .txt file in {}.".format(data_dir))
    return os.path.join(data_dir, txt)

  @property
  def app_url(self):
    """URL that redirects back to the hotel's main page."""
    return flask.url_for("main", hotelname=self.id)

  @property
  def n_reviews(self) -> int:
    """Total number of reviews available for this hotel."""
    return len(self.aspects.data)

  @property
  def n_reviews_aspects_sentiment(self) -> Tuple[int, int, int]:
    aspects_series = self.aspects.aspects_per_review
    valid_words = self.aspects.container.words
    pos, neutral, neg = 0, 0, 0
    for aspect_counter in aspects_series:
      total_sentiment = sum(v for w, v in aspect_counter.items()
                            if w in valid_words)
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
  def encode_plot(*plot):
    return json.dumps(list(plot), cls=plotly.utils.PlotlyJSONEncoder)

  _PIE_COLORS = ["rgb(227,26,28)", "rgb(251,154,153)", "rgb(166,206,227)",
                 "rgb(129,218,85)", "rgb(51,160,44)"]

  @property
  def rating_counts_piechart(self):
    labels, values = [], []
    for l, v in pd.value_counts(self.aspects.data.rating).items():
      labels.append(l)
      values.append(v)
    pie = go.Pie(labels=labels, values=values,
                 marker_colors=self._PIE_COLORS[::-1])
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
    bar = go.Bar(y=categories, x=ratings, orientation="h", width=0.3)
    return self.encode_plot(bar)