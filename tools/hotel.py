import os
import json
import flask
import pandas as pd
from tools import directories, containers

import plotly
from plotly import graph_objects as go

from typing import Any, Dict, Optional


class Hotel:
  """Data structure for a specific Hotel.

  Contains:
    * self.id: An identifier for this particular hotel (id). This is also used
      in the URL of the main hotel page.
    * self.data: DataFrame with all the hotel reviews and the identified aspects.
    * self.aspects: An `AspectsCollection` container for manipulation of aspect
      words.

    Optionally:
      * self.load_name: Name of the pkl/csv file that we used to load the
      review DataFrame.
      * self.{} for all {} that are contained in the hotel json txt.
  """
  # FIXME: Update aspects usage

  def __init__(self, id: str,
               review_data: pd.DataFrame,
               hotel_data: Optional[Dict[str, Any]] = None,
               load_name: Optional[str] = None):
    self.id = id
    self.data = review_data
    self.aspects = containers.AspectsCollection(review_data)

    self.load_name = load_name
    if hotel_data is not None:
      for k, v in hotel_data.items():
        setattr(self, k, v)

  @classmethod
  def load_from_local(cls, folder_name: str, file_name: Optional[str] = None
                      ) -> "Hotel":
    """Loads a hotel using a file (pickle) from local disk."""
    if file_name is None:
      file_name = directories.hotel_db[folder_name]

    # Find file type
    if len(file_name.split(".")) > 1:
      file_type = file_name.split(".")[-1]
    else: # default type is pkl
      file_type = "pkl"
      file_name = ".".join([file_name, file_type])

    # Load DataFrame
    hotel_dir = os.path.join(directories.trip_advisor, folder_name)
    if file_type == "csv":
      review_data = pd.read_csv(os.path.join(hotel_dir, file_name))
    elif file_type == "pkl":
      review_data = pd.read_pickle(os.path.join(hotel_dir, file_name))
    else:
      raise NotImplementedError("File type {} is not supported.".format(
          file_type))

    # Load hotel metadata (star ratings, etc.)
    with open(cls.find_txt(hotel_dir), "r") as file:
      hotel_data = json.load(file)

    return cls(folder_name, review_data, hotel_data, load_name=file_name)

  @classmethod
  def load_from_upload(cls, filename: str) -> "Hotel":
    review_data = pd.read_pickle(os.path.join(directories.upload_path, filename))
    return cls("uploaded_file", review_data)

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