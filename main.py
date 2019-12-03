import os
import flask
import shutil
import tools
import werkzeug
from typing import Optional


app = flask.Flask(__name__)
# Storage directory
app.config["STORAGE_PATH"] = "D:/TripAdvisorReviews/app_storage"
#app.config["STORAGE_PATH"] = "/home/stavros/DATA/TripAdvisorReviews/app_storage"
# Number of aspects to show in `analysis` page
app.config["NUM_ASPECTS"] = 58
# Maximum number of reviews to scrape when a trip advisor link is given.
# This should be removed (or set to None) to scrape all available reviews for
# the given hotel, however then spaCy may take some time to run and we do not
# have a nice loading screen implemented
app.config["MAX_SCRAPE_REVIEWS"] = 10


def scrape(url: str):
  """Scrapes a hotel from Trip Advisor and generates its analysis page."""
  import scraping
  # TODO: Fix case where we already have data for the given URL
  # (currently this should give an error)

  # Add {} url to access review pages
  n = url.find("Reviews") + len("Reviews")
  url = "".join([url[:n], "{}", url[n:]])
  # Scrape reviews
  scraper = scraping.scraper.TripAdvisorScraper(url)
  scraper.scrape_reviews(max_reviews=app.config["MAX_SCRAPE_REVIEWS"])
  scraper.save(app.config["STORAGE_PATH"])
  # Find aspects
  scraping.aspects.find_aspects(scraper.csv_path)
  scraper.remove_csv()
  return flask.redirect(flask.url_for("analysis", hotelname=scraper.lower_name))


@app.route("/analysis/<hotelname>/download")
def download(hotelname: str):
  """Downloads zip file with processed reviews pkl and hotel metadata txt."""
  zip_name = ".".join([hotelname, "zip"])
  zip_path = os.path.join(app.config["STORAGE_PATH"], zip_name)
  if not os.path.exists(zip_path):
    created_zip_path = tools.utils.zipdir(hotelname, app.config["STORAGE_PATH"])
    assert created_zip_path == zip_path

  return flask.send_from_directory(directory=app.config["STORAGE_PATH"],
                                   filename=zip_name,
                                   as_attachment=True)

@app.route("/analysis/<hotelname>/delete")
def delete(hotelname: str):
  """Deletes the hotel from the app storage.

  Deletes both the folder and the zip file of the hotel.
  """
  zip_name = ".".join([hotelname, "zip"])
  zip_path = os.path.join(app.config["STORAGE_PATH"], zip_name)
  if os.path.exists(zip_path):
    os.remove(zip_path)

  folder_path = os.path.join(app.config["STORAGE_PATH"], hotelname)
  if os.path.exists(folder_path):
    shutil.rmtree(folder_path)

  return flask.redirect(flask.url_for("main"))


def view_reviews(word_mode: str, hotel: tools.hotel.Hotel):
  """Generates the reviews page for a given aspect word.

  This is called by `analysis` when a word is given.

  Args:
    word_mode: The word aspect that we want to generate the reviews for.
      This should have the form "{}_{sent}" where {} is the word aspect
      as a str and {sent} can be either 'pos' or 'neg' if the selected word
      was a positive or a negative aspect.
    hotel: Hotel object that we are generating the reviews for.
      This is required because the review page has a link that points back
      to the hotel analysis page.
  """
  word, mode = word_mode.split("__")
  color = tools.containers.get_color(mode == "pos")
  return flask.render_template("reviews.html", hotel=hotel,
                               word=word, mode=mode, color=color)


@app.route("/analysis/<hotelname>?word=<word>")
@app.route("/analysis/<hotelname>")
def analysis(hotelname: str, word: Optional[str] = None):
  """Generates the analysis page (with aspects and visualizations).

  Args:
    hotelname: The hotel id which is the name of the folder that contains
      hotel's data in the STORAGE PATH.
    word: A word aspect for generating the corresponding reviews page.
      See `word_mode` description in `view_reviews` for more details.
  """
  # hotelname is the name of the folder that contains all hotel files
  hotel_path = os.path.join(app.config["STORAGE_PATH"], hotelname)
  hotel = tools.hotel.Hotel.load_from_folder(hotel_path)
  # TODO: Implement word merging
  if word is not None:
    return view_reviews(word, hotel)
  return flask.render_template("analysis.html", hotel=hotel,
                               n_aspects=app.config["NUM_ASPECTS"])


def upload_zip(file: werkzeug.datastructures.FileStorage):
  """Saves and unzips a zip file uploaded by the user."""
  file_path = os.path.join(app.config["STORAGE_PATH"], file.filename)
  file.save(file_path)
  hotel_path = tools.utils.unzip(file_path)
  hotelname = os.path.split(hotel_path)[-1]
  return flask.redirect(flask.url_for("analysis", hotelname=hotelname))


@app.route('/', methods=["GET", "POST"])
def main():
  """Generates main page with available hotels and options to add more."""
  if flask.request.method == "POST":
    if flask.request.form:
      return scrape(flask.request.form["tripadvlink"])

    if flask.request.files:
      return upload_zip(flask.request.files["data"])

  hotels = []
  for file in os.listdir(app.config["STORAGE_PATH"]):
    full_path = os.path.join(app.config["STORAGE_PATH"], file)
    if os.path.isdir(full_path):
      hotels.append(tools.hotel.Hotel.load_from_folder(full_path))

  return flask.render_template("home.html", hotels=hotels)


if __name__ == "__main__":
  app.run(debug=True)