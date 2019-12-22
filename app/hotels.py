import flask
import pandas as pd
from app import db

import json
import plotly
from plotly import graph_objects as go

from typing import Any, Dict


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
  def ratingCounts(self):
    return json.loads(self.ratingCounts_serialized)

  @property
  def languageCounts(self):
    return json.loads(self.languageCounts_serialized)

  @property
  def additionalRatings(self):
    return json.loads(self.additionalRatings_serialized)

  @property
  def app_url(self):
    """URL that redirects back to the hotel's main page."""
    return flask.url_for("main")
    #return flask.url_for("analysis", hotelname=self.id)

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
