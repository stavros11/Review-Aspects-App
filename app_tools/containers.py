import collections
import pandas as pd
from app_tools import hotel
from aspects import containers
from typing import Union, Optional


class AspectWord:
  """Data structure for an aspect WORD.

  Contains:
    * text: The WORD text as str.
    * self.reviews: Dict[Review, float] that contains all reviews that have
      the WORD as an aspect and maps them to the corresponding score.
  """

  def __init__(self, word: str):
    self._text = word
    self.reviews = collections.Counter({})

  def __str__(self):
    return self._text

  def __eq__(self, other: Union[str, "AspectWord"]):
    if isinstance(other, str):
      return str(self) == other
    return self == other

  def __hash__(self):
    return hash(str(self))

  def add_review(self, review: "Review", score: float):
    if review in self.reviews:
      raise KeyError("Review {} already exists in aspect {}".format(
          review, self))
    self.reviews[review] = score


class Review:
  """Data structure for a REVIEW.

  Contains:
    * self.text: The full text of the REVIEW as str.
    * self.aspects: Dict[AspectWord, float] that contains all aspects present
      in REVIEW mapped to their scores.
    * self.index: The index of the REVIEW in the hotel DataFrame.
  """

  def __init__(self, text: str, index: Optional[int] = None):
    self._text = text
    self.index = index
    self.aspects = collections.Counter({})

  def __str__(self):
    return self._text

  def __hash__(self):
    return hash(str(self))

  def add_aspectword(self, word: "AspectWord", score: float):
    if word in self.aspects:
      raise KeyError("Aspect word {} already exists in review {}.".format(
          word, self))
    self.aspects[word] = score


class AspectCollection:

  def __init__(self, reviews: pd.Series, aspects: pd.Series):
    self.reviews = []

    self.known_words = {} # Dict[str, WordAspect]
    self.aspects_scores = collections.Counter({}) # Counter[WordAspect, float]

    for i, (rev, asp) in enumerate(zip(reviews, aspects)):
      self.reviews.append(Review(rev, i))
      for word, score in asp.items():
        if word in self.known_words:
          aspect_word = self.known_words[word]
        else:
          aspect_word = AspectWord(word)
          self.known_words[word] = aspect_word

        self.aspects_scores[aspect_word] += score
        aspect_word.add_review(rev, score)
        self.reviews[-1].add_aspectword(aspect_word, score)
