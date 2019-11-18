"""Tools that collect all aspects of a listing/hotel."""
import collections
import functools
import pickle
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly import subplots
from aspects import distance_matrix
from typing import Dict, Optional, Set


def transform_to_single_words(aspects: collections.Counter
                              ) -> Optional[collections.Counter]:
  try:
    new_aspects = collections.Counter()
    for aspect, score in aspects.items():
      if isinstance(aspect, str):
        for word in aspect.split(" "):
          new_aspects[word] = score
    return new_aspects
  except:
    return None


class AspectContainers:

  def __init__(self,
               neg_scores: collections.Counter,
               pos_scores: collections.Counter,
               neg_appearances: collections.Counter,
               pos_appearances: collections.Counter,
               review_map: Dict[str, collections.Counter]):
    self.map = review_map
    self._pos_scores = pos_scores
    self._neg_scores = neg_scores
    self._pos_appearances = pos_appearances
    self._neg_appearances = neg_appearances
    self.counters = ["_neg_scores", "_pos_scores",
                     "_neg_appearances", "_pos_appearances"]

  def __len__(self) -> int:
    return len(self.appearances)

  @property
  def words(self) -> Set[str]:
    return set(self._pos_scores) | set(self._neg_scores)

  @property
  def appearances(self) -> collections.Counter:
    return self._pos_appearances + self._neg_appearances

  @property
  def scores(self) -> collections.Counter:
    scores = collections.Counter(self._pos_scores)
    scores.update(self._neg_scores)
    return scores

  @property
  def pos_scores(self) -> collections.Counter:
    return self._pos_scores

  @property
  def neg_scores(self) -> collections.Counter:
    return collections.Counter({k: -v for k, v in self._neg_scores.items()})

  @property
  def pos_appearances(self) -> collections.Counter:
    return self._pos_appearances

  @property
  def neg_appearances(self) -> collections.Counter:
    return self._neg_appearances

  def save(self, savedir: str):
    containers = [getattr(self, a) for a in self.counters]
    containers.append(self.map)
    with open(".".join([savedir, "pkl"]), "wb") as file:
      pickle.dump(containers, file)

  @classmethod
  def load(cls, loaddir: str):
    with open(".".join([loaddir, "pkl"]), "rb") as file:
      containers = pickle.load(file)
    return cls(*containers)

  def common_positive(self, start: int = 0, end: int = 30):
    for (word, score) in self.pos_scores.most_common()[start: end]:
      print("{}: {}".format(word, score))

  def common_negative(self, start: int = 0, end: int = 30):
    for (word, score) in self.neg_scores.most_common()[start: end]:
      print("{}: {}".format(word, score))

  def get_figure(self, score_type: str ="scores",
                 start: int = 0, end: int = 20):
    get_bar = functools.partial(self.get_plot_bar, score_type=score_type,
                                start=start, end=end)

    fig = subplots.make_subplots(
        rows=1, cols=2, subplot_titles=("Positive", "Negative"))
    fig.add_trace(get_bar("pos"), row=1, col=1)
    fig.add_trace(get_bar("neg"), row=1, col=2)

    fig.update_layout(
        width=1000,
        height=650,
        font_size=16,
        annotations=[
            go.layout.Annotation(x=0.45, y=-0.15,
                                 showarrow=False,
                                 text="Aspect score")],
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1, # gap between bars of the same location coordinate.
        showlegend=False)
    return fig

  def get_plot_bar(self, sentiment: str = "pos", score_type: str = "scores",
                   start: int = 0, end: int = 20) -> go.Bar:
    aspects = getattr(self, "_".join([sentiment, score_type]))
    bar_plot_words = aspects.most_common()[start: end]
    bar_plot_words = [word for word, _ in bar_plot_words]
    bar_plot_counts = np.array([aspects[word] for word in bar_plot_words])

    name = {"pos": "Positive", "neg": "Negative"}[sentiment]
    return go.Bar(y=bar_plot_words, x=bar_plot_counts,
                  orientation="h", name=name)


class MergedAspectContainers(AspectContainers):

  def __init__(self, word_map: Dict[str, str], *args):
    self.word_map = word_map
    super(MergedAspectContainers, self).__init__(*args)

  @classmethod
  def create(cls, word_map: Dict[str, str], container: AspectContainers):
    new_containers = [collections.Counter() for _ in range(4)]
    new_map = dict()
    for (word, _) in container.appearances.most_common():
      new_word = word_map[word] if word in word_map else word
      # Merge counters
      for i, c in enumerate(container.counters):
        new_containers[i][new_word] += getattr(container, c)[word]
      # Merge map
      if new_word in new_map:
        new_map[new_word].update(container.map[word])
      else:
        new_map[new_word] = container.map[word]

    new_containers.append(new_map)
    return cls(word_map, *new_containers)

  def merge_words(self, word1: str, word2: str):
    """Manually merge of word2 to word1."""
    if word1 in self.words and word2 in self.words:
      # Merge map
      self.map[word1].update(self.map.pop(word2))
      # Merge counters
      for c in self.counters:
        counter = getattr(self, c)
        setattr(self, c, self._merge_words(counter, word1, word2))

  @staticmethod
  def _merge_words(counter: collections.Counter, word1: str, word2: str
                   ) -> collections.Counter:
    if word1 not in counter or word2 not in counter:
      return counter
    counter[word1] += counter.pop(word2)
    return counter


class DataAspects:
  """Collects all identified aspects for a particular hotel or listing."""

  def __init__(self,
               data: pd.DataFrame,
               container: AspectContainers,
               aspect_column_name: str = "aspects"):
    self.data = data
    self.aspect_column = aspect_column_name
    self._container = container
    self.data_dir = None

    self._cut_off = None
    self._matrix = None
    self._merged_container = None

  @classmethod
  def from_dataframe(cls, data: pd.DataFrame,
                     aspect_column_name: str = "aspects"):
    # Transform phrase aspects to single words
    word_aspects = data[aspect_column_name].map(transform_to_single_words)

    review_map = {}
    scores = [collections.Counter(), collections.Counter()]
    appearances = [collections.Counter(), collections.Counter()]
    for i, aspects in enumerate(word_aspects):
      for word, score in aspects.items():
        if isinstance(word, str):
          sign = int(score > 0)
          scores[sign][word] += score
          appearances[sign][word] += 1
          if word in review_map:
            review_map[word][i] += score
          else:
            review_map[word] = collections.Counter({i: score})

    containers = scores + appearances
    containers.append(review_map)
    container = AspectContainers(*containers)
    return cls(data, container, aspect_column_name)

  @classmethod
  def from_pkl(cls, data_dir: str, aspect_column_name: str = "aspects"):
    data = pd.read_pickle(".".join([data_dir, "pkl"]))
    obj = cls.from_dataframe(data, aspect_column_name)
    obj.data_dir = data_dir
    return obj

  @classmethod
  def load(cls, data_dir: str, aspect_column_name: str = "aspects"):
    data = pd.read_pickle(".".join([data_dir, "pkl"]))
    container = AspectContainers.load("_".join([data_dir, "container"]))

    obj = cls(data, container, aspect_column_name)
    obj.data_dir = data_dir

    try:
      matrix = distance_matrix.DistanceMatrix.load(
          "_".join([data_dir, "matrix"]))
      obj.set_distance_matrix(matrix)
    except:
      pass

    return obj

  def save(self):
    if self.data_dir is None:
      raise ValueError("DataAspects save is only available when the data_dir "
                       "attribute is specified.")
    self.container.save("_".join([self.data_dir, "container"]))
    if self.matrix is not None:
      self.matrix.save("_".join([self.data_dir, "matrix"]))

  @property
  def aspects_per_review(self) -> pd.Series:
    return self.data[self.aspect_column]

  @property
  def container(self) -> AspectContainers:
    return self._container

  @property
  def merged_container(self) -> AspectContainers:
    if self._merged_container is None:
      raise ValueError("Merged container is not available.")
    return self._merged_container

  @property
  def cut_off(self) -> AspectContainers:
    if self._cut_off is None:
      raise ValueError("Merge was not called and cut off is not available.")
    return self._cut_off

  @property
  def matrix(self) -> distance_matrix.DistanceMatrix:
    return self._matrix

  @property
  def has_negative(self) -> pd.Series:
    return self.aspects_per_review.map(self._contains_negative)

  def set_distance_matrix(self, matrix: distance_matrix.DistanceMatrix):
    self._matrix = matrix

  def create_distance_matrix(self, model, min_counts: int = -1):
    self._matrix = distance_matrix.DistanceMatrix.calculate(
        model, self.container.appearances, min_counts=min_counts)

  def merge(self, cut_off: float = 0.3):
    if self._matrix is None:
      raise ValueError("Distance matrix not available. Cannot use `merge` "
                       "without a distance matrix.")
    word_map = self._matrix.word_replacement_map(cut_off=cut_off)

    self._cut_off = cut_off
    self._merged_container = MergedAspectContainers.create(
        word_map, self._container)

  @staticmethod
  def _contains_negative(aspects):
    if not aspects:
        return "N/A"
    for v in aspects.values():
        if v < 0: return "Negative"
    return "Positive"