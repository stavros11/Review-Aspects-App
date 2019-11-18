import flask
from application import directories, flask_containers, flask_tools
from aspects import containers
from typing import Optional


def hotels_page():
  hotel_urls = {k: flask.url_for("main", hotelname=v)
                  for k, v in directories.hotel_urls.items()}
  return flask.render_template("hotels.html", hotels=hotel_urls)


def analysis_page(hotelname: str, word: Optional[str] = None):
  aspects, container = flask_containers.load_aspects(hotelname, cut_off=0.3)

  if word is not None:
    return view_reviews_page(hotelname, word, aspects, container)

  pos_aspects = flask_containers.aspects_generator(
      hotelname, word, "pos_scores", container, start=0, end=50)
  neg_aspects = flask_containers.aspects_generator(
      hotelname, word, "neg_scores", container, start=0, end=50)

  return flask.render_template("aspects.html", pos_aspects=pos_aspects,
                               neg_aspects=neg_aspects, hotelname=hotelname)


def view_reviews_page(hotelname: str, word: str,
                      aspects: containers.DataAspects,
                      container: containers.AspectContainers):
  word_reviews = container.map[word]
  df = aspects.data
  for i, score in word_reviews.items():
    reviews = ((df.iloc[i], flask_tools.review_text(df.iloc[i], word), score)
               for i, score in word_reviews.items())

  hotel_url = flask.url_for("main", hotelname=hotelname)
  meta = flask_tools.MetaData(word=word, url=hotel_url, hotelname=hotelname)
  return flask.render_template("reviews.html", reviews=reviews, meta=meta)