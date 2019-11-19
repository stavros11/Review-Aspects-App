import flask
from application import directories, hotel, aspects
from aspects import containers
from typing import Optional


def hotels_page():
  hotels = [hotel.Hotel(k) for k in directories.hotel_order]
  return flask.render_template("hotels.html", hotels=hotels)


def analysis_page(hotelname: str, word: Optional[str] = None):
  # hotelname is the name of the folder that contains all hotel files
  hotel_obj = hotel.Hotel(hotelname)

  # optionally use word2vec to merge words
  hotel_obj.aspects.merge(cut_off=0.4)
  container = hotel_obj.aspects.merged_container
  # alternatively:
  #container = hotel.aspects.container

  if word is not None:
    return view_reviews_page(word, hotel_obj, container)

  pos_aspects = aspects.aspects_generator(
      container, hotel_obj, mode="pos_scores", start=0, end=50)
  neg_aspects = aspects.aspects_generator(
      container, hotel_obj, mode="neg_scores", start=0, end=50)

  return flask.render_template("aspects.html", pos_aspects=pos_aspects,
                               neg_aspects=neg_aspects, hotel=hotel_obj)


def view_reviews_page(word: str,
                      hotel: hotel.Hotel,
                      container: containers.AspectContainers):
  reviews = (aspects.ReviewView(hotel.aspects.data.iloc[i], word)
             for i in container.map[word].keys())
  return flask.render_template("reviews.html", reviews=reviews, word=word,
                               hotel=hotel)