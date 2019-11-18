import flask
from application import directories
from aspects import containers
from typing import Tuple


def load_aspects(hotelname: str, cut_off: float=0.3
                 ) -> Tuple[containers.DataAspects, containers.AspectContainers]:
  aspects = containers.DataAspects.load(directories.hotel_full_dir(hotelname))
  if cut_off is not None:
    aspects.merge(cut_off=cut_off)
    container = aspects.merged_container
  else:
    container = aspects.container

  return aspects, container


def aspects_generator(hotelname, word, mode: "pos_scores",
                      container: containers.AspectContainers,
                      start: int = 0, end: int = 50):
  counter = getattr(container, mode)
  for word, _ in counter.most_common()[start: end]:
    yield Aspect(hotelname, word, container)


class Aspect:

  def __init__(self, hotelname: str, word: str,
               container: containers.AspectContainers):
    self.text = word
    self.hotel = hotelname
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
    return flask.url_for("main", hotelname=self.hotel, word=self.text)