import pandas as pd
from app_tools import hotel
from aspects import containers
from typing import Set

def get_color(score: float):
  return ["Tomato", "MediumSeaGreen"][score > 0]


class ReviewView:

  def __init__(self, data: pd.Series, word: str, valid_words: Set[str]):
    self.word = word
    self.valid_words = valid_words
    for k, v in data.items():
      setattr(self, k, v)

  @property
  def colored_text(self) -> str:
    # Fix new lines for HTML
    text = self.text.replace("\n", "<br>")

    # Color all aspects and bold selected aspect word
    for aspect, score in self.aspects.items():
      color = get_color(score)
      if aspect == self.word:
        text = text.replace(
            "{}".format(aspect),
            "<b><font color='{}'>{}</font></b>".format(color, aspect))
      elif aspect in self.valid_words:
        text = text.replace(
            "{}".format(aspect),
            "<font color='{}'>{}</font>".format(color, aspect))

    return text


def reviews_generator(word: str,
                      container: containers.AspectContainers,
                      hotel: hotel.Hotel,
                      mode: str = "pos_scores") -> ReviewView:
  sign = {"pos_scores": 1, "neg_scores": -1}[mode]
  valid_words = container.words
  for i in container.map[word].keys():
    review = hotel.aspects.data.iloc[i]
    # assert word in review.aspects
    if review.aspects[word] * sign > 0:
      yield ReviewView(review, word, valid_words)