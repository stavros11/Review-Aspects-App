import pandas as pd


class MetaData:

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)


class ReviewView:

  def __init__(self, data: pd.Series, word: str):
    self.word = word
    for k, v in data.items():
      setattr(self, k, v)

  @staticmethod
  def color(score):
    return "MediumSeaGreen" if score > 0 else "Tomato"

  @property
  def colored_text(self) -> str:
    # Fix new lines for HTML
    text = self.text.replace("\n", "<br>")

    # Color all aspects and bold selected aspect word
    for aspect, score in self.aspects.items():
      color = self.color(score)
      if aspect == self.word:
        text = text.replace(
            " {} ".format(aspect),
            " <b><font color='{}'>{}</font></b> ".format(color, aspect))
      else:
        text = text.replace(
            " {} ".format(aspect),
            " <font color='{}'>{}</font> ".format(color, aspect))

    return text