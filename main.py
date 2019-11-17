import flask
import directories
from aspects import flask_containers
app = flask.Flask(__name__)

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


@app.route("/aspects/<hotelname>?word=<word>")
@app.route("/aspects/<hotelname>")
def aspects(hotelname, word=None):
  aspects, container = flask_containers.load_aspects(hotelname, cut_off=0.3)

  start = 0
  end = 30
  if word is None:
    pos_aspects = (flask_containers.Aspect(hotelname, word, container)
                   for word, _ in container.pos_scores.most_common()[start: end])

    neg_aspects = (flask_containers.Aspect(hotelname, word, container)
                   for word, _ in container.neg_scores.most_common()[start: end])
    aspects = zip(pos_aspects, neg_aspects)

    return flask.render_template("aspects.html", aspects=aspects)

  word_reviews = container.map[word]
  df = aspects.data
  for i, score in word_reviews.items():
    reviews = ((df.iloc[i], review_text(df.iloc[i], word), score)
               for i, score in word_reviews.items())

  hotel_url = flask.url_for("aspects", hotelname=hotelname)
  meta = MetaData(word=word, url=hotel_url, hotelname=hotelname)
  return flask.render_template("reviews.html", reviews=reviews, meta=meta)


@app.route('/')
def hotels():
  hotel_urls = {k: flask.url_for("aspects", hotelname=v)
                for k, v in directories.hotel_urls.items()}
  return flask.render_template("hotels.html", hotels=hotel_urls)


if __name__ == "__main__":
  app.run(debug=True)