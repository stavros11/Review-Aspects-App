import os
import json
import flask
from application import directories
from aspects import containers

import plotly
from plotly import graph_objects as go

from typing import Optional


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
  def n_reviews(self):
    return sum(self.ratingCounts)

  @property
  def rating_counts_barplot(self):
    # orientation='h' for horizontal bars
    n = len(self.ratingCounts)
    bar = go.Bar(x=list(range(1, n + 1)), y=self.ratingCounts, name="Rating Counts")
    graph_json = json.dumps([bar], cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


def aspects_generator(word: str, hotel_id: str,
                      container: containers.AspectContainers,
                      mode: str = "pos_scores", start: int = 0, end: int = 50):
  counter = getattr(container, mode)
  for word, _ in counter.most_common()[start: end]:
    yield Aspect(word, hotel_id, container)