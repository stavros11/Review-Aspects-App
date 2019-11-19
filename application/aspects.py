import flask
import pandas as pd
from application import hotel
from aspects import containers


class MetaData:

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)


class Aspect:

  def __init__(self, word: str, hotel: hotel.Hotel,
               container: containers.AspectContainers,
               mode: str = "pos_scores"):
    self.text = word
    self.hotel = hotel
    self.container = container
    self.mode = mode

  @property
  def score(self) -> float:
    return getattr(self.container, self.mode)[self.text]

  @property
  def pos_appearances(self) -> int:
    return self.container.pos_appearances[self.text]

  @property
  def pos_percentage(self) -> float:
    return 100.0 * self.pos_appearances / self.hotel.n_data_reviews

  @property
  def neg_percentage(self) -> float:
    return 100.0 * self.neg_appearances / self.hotel.n_data_reviews

  @property
  def neg_appearances(self) -> int:
    return self.container.neg_appearances[self.text]

  @property
  def url(self) -> str:
    return flask.url_for("main", hotelname=self.hotel.id, word=self.text)


def aspects_generator(container: containers.AspectContainers,
                      hotel: hotel.Hotel,
                      mode: str = "pos_scores",
                      start: int = 0, end: int = 50):
  counter = getattr(container, mode)
  for word, _ in counter.most_common()[start: end]:
    yield Aspect(word, hotel, container, mode=mode)


class ReviewView:

  def __init__(self, data: pd.Series, word: str):
    self.word = word
    for k, v in data.items():
      setattr(self, k, v)

  @staticmethod
  def color(score):
    return "MediumSeaGreen" if score > 0 else "Tomato"

  @property
  def colored_text(self) -> str:
    # Fix new lines for HTML
    text = self.text.replace("\n", "<br>")

    # Color all aspects and bold selected aspect word
    for aspect, score in self.aspects.items():
      color = self.color(score)
      if aspect == self.word:
        text = text.replace(
            " {} ".format(aspect),
            " <b><font color='{}'>{}</font></b> ".format(color, aspect))
      else:
        text = text.replace(
            " {} ".format(aspect),
            " <font color='{}'>{}</font> ".format(color, aspect))

    return text