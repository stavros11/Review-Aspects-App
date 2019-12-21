import os
import json
import flask
import pandas as pd
from tools import containers, utils

import plotly
from plotly import graph_objects as go

from typing import Any, Dict


class Hotel:
  """Data structure for a specific Hotel.

  Contains:
    * self.id: An identifier for this particular hotel (id). This is also used
      in the URL of the main hotel page.
    * self.data: DataFrame with all the hotel reviews and the identified aspects.
    * self.aspects: An `AspectsCollection` container for manipulation of aspect
      words.

    Optionally:
      * self.{} for all {} that are contained in the hotel json txt.
  """

  def __init__(self, metadata: Dict[str, Any], review_data: pd.DataFrame):
    if "id" not in metadata:
      raise KeyError("Unable to find hotel id in hotel meta data file.")
    for k, v in metadata.items():
      setattr(self, k, v)

    self.data = review_data
    self.unigrams = containers.nGrams.unigrams(review_data)


  @classmethod
  def load_from_folder(cls, folder: str) -> "Hotel":
    if not os.path.isdir(folder):
      raise FileNotFoundError("Unable to find directory {}.".format(folder))

    # Load hotel metadata (star ratings, etc.)
    metafile_dir = utils.find_files_of_type(folder, target_type="txt")
    if len(metafile_dir) > 1:
      raise FileExistsError("Multiple txt files found in {}.".format(folder))
    elif len(metafile_dir) == 0:
      raise FileNotFoundError("Unable to find txt file in {}.".format(folder))
    with open(metafile_dir[0], "r") as file:
      metadata = json.load(file)

    # Load DataFrame from csv/pkl
    pkl_files = utils.find_files_of_type(folder, target_type="pkl")
    csv_files = utils.find_files_of_type(folder, target_type="csv")
    if len(csv_files) + len(pkl_files) > 1:
      raise FileExistsError("Multiple data files found in {}.".format(folder))
    elif len(csv_files) + len(pkl_files) == 0:
      raise FileNotFoundError("Unable to data file in {}.".format(folder))

    if len(pkl_files) > 0:
      review_data = pd.read_pickle(pkl_files[0])
    else:
      review_data = pd.read_csv(csv_files[0])

    # If the key `id` is not found in metadata use the folders name
    # The `id` key is required to generate URLs
    if "id" not in metadata:
      metadata["id"] = os.path.split(folder)[-1]

    return cls(metadata, review_data)

  @property
  def app_url(self):
    """URL that redirects back to the hotel's main page."""
    return flask.url_for("analysis", hotelname=self.id)

  @property
  def n_reviews(self) -> int:
    """Total number of reviews available for this hotel."""
    return len(self.data)

  @staticmethod
  def encode_plot(*plot):
    return json.dumps(list(plot), cls=plotly.utils.PlotlyJSONEncoder)

  _PIE_COLORS = ["rgb(227,26,28)", "rgb(251,154,153)", "rgb(166,206,227)",
                 "rgb(129,218,85)", "rgb(51,160,44)"]

  @property
  def rating_counts_piechart(self):
    labels, values = [], []
    for l, v in pd.value_counts(self.data.rating).items():
      labels.append(l)
      values.append(v)
    pie = go.Pie(labels=labels, values=values,
                 marker_colors=self._PIE_COLORS[::-1])
    return self.encode_plot(pie)

  @property
  def aspects_sentiment_piechart(self):
    labels = ["Negative", "Neutral", "Positive"]
    colors = [self._PIE_COLORS[0], self._PIE_COLORS[2], self._PIE_COLORS[-1]]
    pie = go.Pie(labels=labels, values=self.aspects.n_reviews_aspects_sentiment,
                 marker_colors=colors)
    return self.encode_plot(pie)

  @property
  def additionalrating_radarchart(self):
    """NOT USED"""
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
