import collections
import flask
from app_tools import hotel
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
    return self.container.scores[self.text]
    #return getattr(self.container, self.mode)[self.text]

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
    word_mode = "__".join([self.text, self.mode])
    return flask.url_for("main", hotelname=self.hotel.id, word=word_mode)


def aspects_generator(container: containers.AspectContainers,
                      hotel: hotel.Hotel,
                      mode: str = "pos_scores",
                      start: int = 0, end: int = 50):
  #counter = getattr(container, mode)
  counter = container.scores
  if mode == "neg_scores":
    counter = collections.Counter({k: -v for k, v in counter.items()})

  for word, _ in counter.most_common()[start: end]:
    yield Aspect(word, hotel, container, mode=mode)