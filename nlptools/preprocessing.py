import os
import re
import json
import spacy
import time
import pandas as pd
from spacy import tokens
from typing import Iterable, List

_CMAP_DIR = os.path.join(os.getcwd(), "scraping", "contractions.txt")
with open(_CMAP_DIR, "r") as file:
  _CMAP = json.load(file)


def expand_contractions(text, contraction_mapping=_CMAP):
  contractions_pattern = re.compile('({})'.format('|'.join(
      contraction_mapping.keys())), flags=re.IGNORECASE|re.DOTALL)

  def expand_match(contraction):
    match = contraction.group(0)
    first_char = match[0]
    if contraction_mapping.get(match):
      expanded_contraction = contraction_mapping.get(match)
    else:
      expanded_contraction = contraction_mapping.get(match.lower())
    expanded_contraction = first_char+expanded_contraction[1:]
    return expanded_contraction

  expanded_text = contractions_pattern.sub(expand_match, text)
  expanded_text = re.sub("'s", "", expanded_text)
  expanded_text = re.sub("'", "", expanded_text)
  return expanded_text


def remove_special_characters(text: str, remove_digits: bool = False) -> str:
  if remove_digits:
    pattern = r"[^.a-zA-z\s]"
  else:
    pattern = r"[^a-zA-z0-9.!?\s]"

  # Substitute all special characters with spaces
  text = re.sub(pattern, " ", text)
  # Substitute any white space character with a single space
  text = " ".join(text.split())
  return text


def find_language(text: str) -> str:
  try:
    language = langdetect.detect(text)
  except:
    print("Failed to identify language of:", text)
    return "<UNK>"
  return language


def basic_preprocessing(texts: pd.Series):
  texts = texts.map(expand_contractions)
  texts = texts.map(remove_special_characters)
  print("Basic preprocessing completed on {} reviews.".format(len(texts)))
  return texts


def lemmatize(docs: Iterable[tokens.Doc]) -> List[str]:
  texts = []
  start_time = time.time()

  for doc in docs:
    text = " ".join([token.lemma_ if token.lemma_ != '-PRON-' else token.text
                     for token in doc])
    # Leave only letter characters
    text = re.sub("[^a-zA-z\s]", " ", text)
    # Substitute any white space character with a single space
    text = " ".join(text.split())
    # Make lower case
    texts.append(text.lower())

  print("\nLemmatized {} reviews.".format(len(texts)))
  print(time.time() - start_time)
  return texts


def apply_spacy(texts: Iterable[str], parse=True, tag=True, entity=True
                ) -> Iterable[tokens.Doc]:
  nlp = spacy.load('en_core_web_sm', parse=parse, tag=tag, entity=entity)

  start_time = time.time()
  docs = list(nlp.pipe(texts))
  print("\nApplied spacy on {} reviews.".format(len(docs)))
  print(time.time() - start_time)

  return docs