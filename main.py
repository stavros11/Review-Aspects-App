import os
import flask
import tools
from typing import Optional


app = flask.Flask(__name__)
storage_path = "D:/TripAdvisorReviews/app_storage"


def view_reviews(word_mode: str, hotel: tools.hotel.Hotel):
  """Generates the reviews page for a given aspect word."""
  word, mode = word_mode.split("__")
  color = tools.containers.get_color(mode == "pos")
  return flask.render_template("reviews.html", hotel=hotel,
                               word=word, mode=mode, color=color)


def analysis_from_upload(filename):
  hotel = tools.hotel.Hotel.load_from_upload(filename)
  return flask.render_template("analysis.html", hotel=hotel, n_aspects=58)


@app.route("/<hotelname>?word=<word>")
@app.route("/<hotelname>")
def analysis(hotelname: str, word: Optional[str] = None):
  """Generates the analysis page (with aspects and visualizations)."""
  # hotelname is the name of the folder that contains all hotel files
  hotel_path = os.path.join(storage_path, hotelname)
  hotel = tools.hotel.Hotel.load_from_folder(hotel_path)
  # TODO: Implement word merging
  if word is not None:
    return view_reviews(word, hotel)

  return flask.render_template("analysis.html", hotel=hotel, n_aspects=58)


@app.route('/', methods=["GET", "POST"])
def main():
  """Generates main page with available hotel photos."""
  if flask.request.method == "POST" and flask.request.files:
    file = flask.request.files["data"]
    file.save(os.path.join(tools.directories.upload_path, file.filename))
    return analysis_from_upload(file.filename)

  hotels = []
  for file in os.listdir(storage_path):
    full_path = os.path.join(storage_path, file)
    if os.path.isdir(full_path):
      hotels.append(tools.hotel.Hotel.load_from_folder(full_path))

  return flask.render_template("hotels.html", hotels=hotels)


if __name__ == "__main__":
  app.run(debug=True)