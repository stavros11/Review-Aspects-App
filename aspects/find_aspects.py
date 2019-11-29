import collections
import os
import time
from app_tools import directories
from spacy import tokens
from typing import Iterable, List, Set


def load_words(filename: str) -> Set[str]:
    """Loads opinion word from txt file to set."""
    file = open(os.path.join(directories.opinion_lexicon, filename),
                encoding="ISO-8859-1")
    return set(line.strip() for line in file.readlines())


_POS_WORDS = load_words("pos_words.txt")
_NEG_WORDS = load_words("neg_words.txt")
_OPINION_WORDS = _POS_WORDS | _NEG_WORDS


def _is_opinion_mod(token: tokens.Token) -> bool:
  """Helper method for `sentiment_aspects`."""
  is_mod = token.dep_ in {"amod", "advmod"}
  is_op = token.text.lower() in _OPINION_WORDS
  return is_mod and is_op


def sentiment_aspects(docs: Iterable[tokens.Doc]) -> List[collections.Counter]:
  """Finds feature words and the corresponding sentiment.

    Example use:
    feature_sentiment("The pillows were very uncomfortable. "
                        "Location was great")
    Returns: Counter({location: 1, pillows: -1})

  Args:
    sentence: A review text. Can have more than one sentence, for example
        can be a full review comment.

  Returns:
    A counter where keys are the features and the values are the
      corresponding sentiment scores.
  """
  sent_dict_list = []
  start_time = time.time()

  for doc in docs:
    sent_dict = collections.Counter()
    for token in doc:
      # check if the word is an opinion word, then assign sentiment
      if token.text.lower() in _OPINION_WORDS:
        sentiment = 1 if token.text.lower() in _POS_WORDS else -1
        if (token.dep_ == "advmod"):
          # if target is an adverb modifier (i.e. pretty, highly, etc.)
          # but happens to be an opinion word, ignore and pass
          continue

        elif (token.dep_ == "amod"):
          sent_dict[token.head.text.lower()] += sentiment

        else:
          for child in token.children:
            # if there's a adj modifier (i.e. very, pretty, etc.) add
            # more weight to sentiment
            # This could be better updated for modifiers that either
            # positively or negatively emphasize
            if _is_opinion_mod(child):
              sentiment *= 1.5
            # check for negation words and flip the sign of sentiment
            if child.dep_ == "neg":
              sentiment *= -1
          for child in token.children:
            if (token.pos_ == "VERB") & (child.dep_ == "dobj"):
              # if verb, check if there's a direct object
              sent_dict[child.text.lower()] += sentiment
              # check for conjugates (a AND b), then add both to dictionary
              subchildren = []
              conj = 0
              for subchild in child.children:
                if subchild.text.lower() == "and": conj=1
                if (conj == 1) and (subchild.text.lower() != "and"):
                  subchildren.append(subchild.text.lower())
                  conj = 0
              for subchild in subchildren:
                sent_dict[subchild] += sentiment

          # check for negation
          for child in token.head.children:
            noun = ""
            if _is_opinion_mod(child):
              sentiment *= 1.5
            if (child.dep_ == "neg"):
              # check for negation words and flip the sign of sentiment
              sentiment *= -1

          # check for nouns
          for child in token.head.children:
            noun = ""
            if (child.pos_ == "NOUN") and (child.text not in sent_dict):
              noun = child.text.lower()
              # Check for compound nouns
              for subchild in child.children:
                if subchild.dep_ == "compound":
                  noun = subchild.text.lower() + " " + noun
                  sent_dict[noun] += sentiment
    sent_dict_list.append(collections.Counter(sent_dict))

  print("\nFound aspects on {} reviews.".format(len(sent_dict_list)))
  print(time.time() - start_time)
  return sent_dict_list