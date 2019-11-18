def review_text(series, word: str) -> str:
  text = series.text.replace("\n", "<br>")
  for aspect in series.aspects:
    text = text.replace(aspect, "<b>{}</b>".format(aspect))
  text = text.replace(word, "<font color='Tomato'>{}</font>".format(word))
  return text


class MetaData:

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)