import flask
from application import directories, flask_containers, flask_tools
from aspects import containers
from typing import Optional


def hotels_page():
  hotels = [flask_containers.Hotel(k) for k in directories.hotel_order]
  return flask.render_template("hotels.html", hotels=hotels)


def analysis_page(hotelname: str, word: Optional[str] = None):
  # hotelname is the name of the folder that contains all hotel files
  hotel = flask_containers.Hotel(hotelname)

  # optionally use word2vec to merge words
  hotel.aspects.merge(cut_off=0.4)
  container = hotel.aspects.merged_container
  # alternatively: container = hotel.aspects.container

  if word is not None:
    return view_reviews_page(word, hotel, container)

  pos_aspects = flask_containers.aspects_generator(
      word, hotel.id, container, "pos_scores", start=0, end=50)
  neg_aspects = flask_containers.aspects_generator(
      word, hotel.id, container, "neg_scores", start=0, end=50)

  return flask.render_template("aspects.html", pos_aspects=pos_aspects,
                               neg_aspects=neg_aspects, hotel=hotel)


def view_reviews_page(word: str,
                      hotel: flask_containers.Hotel,
                      container: containers.AspectContainers):
  reviews = (flask_tools.ReviewView(hotel.aspects.data.iloc[i], word)
             for i in container.map[word].keys())
  return flask.render_template("reviews.html", reviews=reviews, word=word,
                               hotel=hotel)