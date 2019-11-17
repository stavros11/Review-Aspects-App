"""Distance matrix for finding similar words using word2vec."""
import collections
import pickle
import numpy as np
from typing import Dict, List, Tuple


class DistanceMatrix:

  def __init__(self, words: List[str], matrix: np.ndarray):
    """Constructor."""
    assert len(words) == len(matrix)
    assert matrix.shape[0] == matrix.shape[1]
    assert len(matrix.shape) == 2

    self.words = words
    self.matrix = matrix

  @classmethod
  def calculate(cls, model, aspects: collections.Counter, min_counts: int = -1):
    """Constructs word distance matrix from aspects counter."""
    words = []
    not_in_model = []
    n_smaller_count = 0
    for (word, counts) in aspects.most_common():
      if counts <= 0:
        raise ValueError("Word {} has {} <= 0 value in the counter. "
                         "Distance matrix requires positive values "
                         "only.".format(word, counts))
      if counts > min_counts:
        if word in model:
          words.append(word)
        else:
          not_in_model.append(word)
      else:
        n_smaller_count += 1

    print("{} valid words not in the Word2Vec model.".format(len(not_in_model)))
    print("{} words have count < {} and are ignored.".format(
        n_smaller_count, min_counts))
    print("Calculating matrix with {} words.".format(len(words)))
    matrix = np.eye(len(words))
    for i, word in enumerate(words):
      matrix[i, i:] = model.distances(word, words[i:])

    return cls(words, matrix)

  def save(self, savedir: str):
    with open("_".join([savedir, "words.pkl"]), "wb") as file:
      pickle.dump(self.words, file)
    np.save("{}.npy".format(savedir), self.matrix)

  @classmethod
  def load(cls, loaddir: str):
    with open("_".join([loaddir, "words.pkl"]), "rb") as file:
      words = list(pickle.load(file))
    matrix = np.load("{}.npy".format(loaddir))
    return cls(words, matrix)

  def __len__(self) -> int:
    return len(self.words)

  def __getitem__(self, i: int) -> Tuple[str, np.ndarray]:
    return (self.word[i], self.matrix[i])

  @property
  def values(self):
    ids = np.triu_indices(len(self.matrix), k=1)
    return self.matrix[ids]

  def describe(self):
    print("Mean:", self.values.mean())
    print("STD:", self.values.std())
    print("Min:", self.values.min())
    print("Max:", self.values.max())

  def count_words_closer_than(self, cut_off: float) -> int:
    return (self.values < cut_off).sum()

  def similar_words(self, cut_off: float) -> List[Tuple[str, str]]:
    ids = np.triu_indices(len(self.matrix), k=1)
    ind = np.where(self.matrix[ids] < cut_off)[0]
    sim_words = [(self.words[ids[0][i]], self.words[ids[1][i]]) for i in ind]
    return sim_words

  def word_replacement_map(self, cut_off: float) -> Dict[str, str]:
    """Maps each word to the equivalent one with the highest count."""
    word_replacement_map = {}
    for i, word in enumerate(self.words):
      if word not in word_replacement_map:
        word_replacement_map[word] = word
        for j in np.where(self.matrix[i] < cut_off)[0]:
          if self.words[j] not in word_replacement_map:
            word_replacement_map[self.words[j]] = word
    return word_replacement_map