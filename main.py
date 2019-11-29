import flask
import app_tools as tools
from typing import Optional


app = flask.Flask(__name__)


def hotels_page():
  hotels = [tools.hotel.Hotel.load_from_local(k)
            for k in tools.directories.hotel_order]
  return flask.render_template("hotels.html", hotels=hotels)


def analysis_page(hotelname: str, word: Optional[str] = None):
  # hotelname is the name of the folder that contains all hotel files
  hotel = tools.hotel.Hotel.load_from_local(hotelname)

  # optionally use word2vec to merge words
  #hotel.aspects.merge(cut_off=0.4)
  #container = hotel.aspects.merged_container
  # alternatively:
  #container = hotel.aspects.container

  #if word is not None:
  #  return view_reviews_page(word, hotel, container)

  return flask.render_template("aspects.html", hotel=hotel, n_aspects=58)


#def view_reviews_page(word_mode: str,
#                      hotel: tools.hotel.Hotel,
#                      container: containers.AspectContainers):
#  word, mode = word_mode.split("__")
#  color = tools.reviews.get_color(int(mode == "pos_scores")) # title color
#  reviews = tools.reviews.reviews_generator(word, container, hotel, mode)
#  return flask.render_template("reviews.html", reviews=reviews, word=word,
#                               hotel=hotel, title_color=color)


@app.route("/<hotelname>?word=<word>")
@app.route("/<hotelname>")
@app.route('/')
def main(hotelname=None, word=None):
  if hotelname is None:
    return hotels_page()
  return analysis_page(hotelname, word)


if __name__ == "__main__":
  app.run(debug=True)