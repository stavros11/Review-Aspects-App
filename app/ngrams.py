import pandas as pd
from app import models
from app import stopwords
from typing import Dict, List

VALID_UNIGRAM_POS_ = {"NOUN", "PROPN"}


def create_unigrams(reviews: pd.DataFrame, hotel_id: str) -> Dict[str, models.Unigram]:
  word_to_db = {}
  for _, review in reviews.iterrows():
    for pos, sent in enumerate(review.spacy_text.sents):
      for token in sent:
        text = token.text.lower()
        sent_id = models.Sentence.generate_id(review.id, pos)
        if (len(text) > 1 and text not in stopwords.INVALID_TOKENS
            and token.pos_ in VALID_UNIGRAM_POS_):
          if text in word_to_db:
            word_to_db[text].sentences.append(sent_id)
          else:
            word_to_db[text] = models.Unigram(text=text, hotelId=hotel_id)
            word_to_db[text].sentences.append(sent_id)
  return word_to_db
