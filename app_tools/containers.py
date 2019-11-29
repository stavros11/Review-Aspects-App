import collections
import pandas as pd
from typing import Any, Dict, List, Set, Union


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

  @property
  def text(self) -> str:
    return str(self)

  @property
  def positive_appearances(self) -> int:
    return sum(score > 0 for score in self.reviews.values())

  @property
  def negative_appearances(self) -> int:
    return sum(score < 0 for score in self.reviews.values())

  @property
  def score(self) -> float:
    return sum(self.reviews.values())

  def get_reviews(self, mode: str = "pos") -> "Review":
    sign = 1 if mode == "pos" else - 1
    for review, score in self.reviews.items():
      if sign * score > 0:
        yield review


class Review:
  """Data structure for a REVIEW.

  Contains:
    * self.text: The full text of the REVIEW as str.
    * self.aspects: Dict[AspectWord, float] that contains all aspects present
      in REVIEW mapped to their scores.
    * self.index: The index of the REVIEW in the hotel DataFrame.
  """

  def __init__(self, text: str, meta: Dict[str, Any]):
    self._text = text
    self.aspects = collections.Counter({})
    for k, v in meta.items():
      setattr(self, k, v)

  def __str__(self):
    return self._text

  def __hash__(self):
    return hash(str(self))

  def add_aspectword(self, word: "AspectWord", score: float):
    if word in self.aspects:
      raise KeyError("Aspect word {} already exists in review {}.".format(
          word, self))
    self.aspects[word] = score

  @property
  def score(self) -> float:
    return sum(self.aspects.values())

  @property
  def colored_text(self) -> str:
    # TODO: Implement this properly.
    return str(self)


_DEFAULT_REVIEW_META = {"absoluteUrl", "title", "publishedDate", "rating",
                        "helpfulVotes", "username", "user_hometownName"}

class AspectsCollection:
  """Data structure that handles `AspectWord` and `Review` collections.

  Contains:
    * self.reviews: List of `Review` with the ordering of the DataFrame.
    * known_words: Dict from words (str) to the corresponding `AspectWord`.
    * aspects_scores: Dict from `AspectWord` to its corresponding score.
  """

  def __init__(self, data: pd.DataFrame,
               text_col_name: str = "text",
               aspect_col_name: str = "aspects",
               review_meta: Set[str] = _DEFAULT_REVIEW_META):
    self.reviews = []

    self.known_words = {} # Dict[str, WordAspect]
    self.aspects_scores = collections.Counter({}) # Counter[WordAspect, float]

    iterator = zip(data[text_col_name], data[aspect_col_name])
    for i, (review_text, aspect_counter) in enumerate(iterator):
      if aspect_counter is None:
        continue

      meta = {k: data.iloc[i][k] for k in review_meta}
      meta["index"] = i
      review = Review(review_text, meta)
      self.reviews.append(review)

      for word, score in aspect_counter.items():
        if word in self.known_words:
          aspect = self.known_words[word]
        else:
          aspect = AspectWord(word)
          self.known_words[word] = aspect

        self.aspects_scores[aspect] += score

        aspect.add_review(review, score)
        review.add_aspectword(aspect, score)

  def most_common(self, invert_sign: bool = False) -> List[AspectWord]:
    if invert_sign:
      score_counter = collections.Counter(
          {k: -v for k, v in self.aspects_scores.items()})
    else:
      score_counter = self.aspects_scores

    return [w for w, _ in score_counter.most_common()]

  @property
  def n_reviews(self):
    return len(self.reviews)

  @property
  def most_common_positive(self) -> List[AspectWord]:
    return self.most_common(invert_sign=False)

  @property
  def most_common_negative(self) -> List[AspectWord]:
    return self.most_common(invert_sign=True)

  @property
  def n_reviews_aspects_sentiment(self) -> List[int]:
    """Calculates the number of reviews with neg/neutral/pos total score."""
    pos = sum(review.score > 0 for review in self.reviews)
    neutral = sum(review.score == 0 for review in self.reviews)
    neg = sum(review.score < 0 for review in self.reviews)
    return [neg, neutral, pos]