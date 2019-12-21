import collections
import pandas as pd
import spacy
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tools import stopwords
from typing import Any, Dict, List, Sequence


SID = SentimentIntensityAnalyzer()


def get_color(positive: bool = True) -> str:
  return "MediumSeaGreen" if positive else "Tomato"


class Sentence:

  def __init__(self, sentence: spacy.tokens.Span, token: spacy.tokens.Token,
               review: pd.Series):
    self.sentence = sentence
    self.tokens = [token]
    self.review = review
    self.sentiment = SID.polarity_scores(sentence.text)

  def append(self, token: spacy.tokens.Token):
    self.tokens.append(token)

  @property
  def text(self) -> str:
    return self.sentence.text

  def __str__(self) -> str:
    return self.text

  def __hash__(self):
    return hash(str(self))

  @property
  def colored(self) -> str:
    color = "SlateBlue"
    text = self.sentence.text
    for token in self.tokens:
      word = token.text
      colored_word = "<b><font color='{}'>{}</font></b>".format(color, word)
      text = text.replace(word, colored_word)
    return text

  @property
  def polarity(self) -> str:
    if self.sentiment["compound"] > 0.2:
      return "pos"
    elif self.sentiment["compound"] < -0.2:
      return "neg"
    return "neu"


class SentenceCollection:

  def __init__(self, word: str, sentences: Sequence[Sentence]):
    if isinstance(sentences, Sentence):
      self.list = [sentences]
    else:
      self.list = list(sentences)
    self.word = word

    self.pos = collections.Counter()
    self.neu = collections.Counter()
    self.neg = collections.Counter()
    self.sentiment_counter = {"pos": 0, "neu": 0, "neg": 0}
    self.sentiment_scores = {}
    for sentence in self.list:
      polarity = sentence.polarity
      getattr(self, polarity)[sentence] += sentence.sentiment[polarity]
      self.sentiment_scores[sentence] = sentence.sentiment["compound"]
      self.sentiment_counter[polarity] += 1

  def append(self, sentence: Sentence):
    if sentence in self.sentiment_scores:
      raise ValueError("Sentence {} already exists in collection."
                       "".format(sentence))

    self.list.append(sentence)
    polarity = sentence.polarity
    getattr(self, polarity)[sentence] += sentence.sentiment[polarity]
    self.sentiment_scores[sentence] = sentence.sentiment["compound"]
    self.sentiment_counter[polarity] += 1

  def __getitem__(self, i: int) -> Sentence:
    return self.list[i]

  def __len__(self) -> int:
    return len(self.list)

  def __iter__(self) -> Sentence:
    for sentence in self.list:
      yield sentence


class nGrams:

  def __init__(self, sentences: Dict[str, SentenceCollection]):
    self.sentences = sentences
    self.appearances = collections.Counter(
        {k: len(v) for k, v in sentences.items()})


  @classmethod
  def unigrams(cls, data: pd.DataFrame) -> "nGrams":
    """Creates dict from unigrams to spacy tokens"""
    word_to_sentences = {}
    for i, doc in enumerate(data.spacy_text):
      review = data.iloc[i]
      for token in doc:
        text = token.text.lower()
        if len(text) > 1 and text not in stopwords.INVALID_TOKENS:
          sentence = token.sent
          if text in word_to_sentences:
            if sentence == word_to_sentences[text][-1].sentence:
              word_to_sentences[text][-1].append(token)
            else:
              word_to_sentences[text].append(Sentence(sentence, token, review))
          else:
            word_to_sentences[text] = SentenceCollection(
                text, Sentence(sentence, token, review))
    return cls(word_to_sentences)
