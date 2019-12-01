import os
import flask
import tools
from typing import Optional


app = flask.Flask(__name__)
#STORAGE_PATH = "D:/TripAdvisorReviews/app_storage"
STORAGE_PATH = "/home/stavros/DATA/TripAdvisorReviews/app_storage"
NUM_ASPECTS = 58


def view_reviews(word_mode: str, hotel: tools.hotel.Hotel):
  """Generates the reviews page for a given aspect word."""
  word, mode = word_mode.split("__")
  color = tools.containers.get_color(mode == "pos")
  return flask.render_template("reviews.html", hotel=hotel,
                               word=word, mode=mode, color=color)


def upload_zip(file):
  # TODO: Fix typing (from Werkzeug)
  file_path = os.path.join(STORAGE_PATH, file.filename)
  file.save(file_path)
  hotel_path = tools.utils.unzip(file_path)
  hotelname = os.path.split(hotel_path)[-1]
  return flask.redirect(flask.url_for("analysis", hotelname=hotelname))


def scrape(url: str):
  # TODO: Fix case where we already have data for the given URL
  # (currently this should give an error)
  n = url.find("Reviews") + len("Reviews")
  url = "".join([url[:n], "{}", url[n:]])
  scraper = tools.scraper.TripAdvisorScraper(url)
  scraper.scrape_reviews(max_reviews=10)
  scraper.save(STORAGE_PATH)
  return flask.redirect(flask.url_for("analysis", hotelname=scraper.lower_name))


@app.route("/<hotelname>?word=<word>")
@app.route("/<hotelname>")
def analysis(hotelname: str, word: Optional[str] = None):
  """Generates the analysis page (with aspects and visualizations)."""
  # hotelname is the name of the folder that contains all hotel files
  hotel_path = os.path.join(STORAGE_PATH, hotelname)
  hotel = tools.hotel.Hotel.load_from_folder(hotel_path)
  # TODO: Implement word merging
  if word is not None:
    return view_reviews(word, hotel)

  return flask.render_template("analysis.html", hotel=hotel, n_aspects=NUM_ASPECTS)


@app.route('/', methods=["GET", "POST"])
def main():
  """Generates main page with available hotel photos."""
  if flask.request.method == "POST":
    if flask.request.form:
      # TODO: Fix this to scrape instead of redirecting
      return scrape(flask.request.form["tripadvlink"])

    if flask.request.files:
      return upload_zip(flask.request.files["data"])

  hotels = []
  for file in os.listdir(STORAGE_PATH):
    full_path = os.path.join(STORAGE_PATH, file)
    if os.path.isdir(full_path):
      hotels.append(tools.hotel.Hotel.load_from_folder(full_path))

  return flask.render_template("home.html", hotels=hotels)


if __name__ == "__main__":
  app.run(debug=True)