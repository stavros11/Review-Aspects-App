import flask
import flask_sqlalchemy
import flask_migrate


# Define app
app = flask.Flask(__name__)
# Storage directory
app.config["STORAGE_PATH"] = "/home/stavros/DATA/TripAdvisorReviews/app_storage"
# Configure SQL SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}/app.db".format(
    app.config["STORAGE_PATH"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Number of aspects to show in `analysis` page
app.config["NUM_ASPECTS"] = 58
# Define database
db = flask_sqlalchemy.SQLAlchemy(app)

migrate = flask_migrate.Migrate(app, db)


import os
import werkzeug
from app import models
from app import utils
from typing import Optional


def upload_zip(file: werkzeug.datastructures.FileStorage):
  """Saves and unzips a zip file uploaded by the user."""
  file_path = os.path.join(app.config["STORAGE_PATH"], file.filename)
  file.save(file_path)

  # Unzip the file and remove the zip
  hotel_path = utils.unzip(file_path)
  os.remove(file_path)

  # Read reviews and meta data from files and remove the directory
  hotel_id = os.path.split(hotel_path)[-1]
  meta = utils.read_metadata(hotel_path)
  reviews = utils.read_reviews(hotel_path)
  os.rmdir(hotel_path)

  # Add hotel to database
  hotel = models.Hotel.create(hotel_id, meta)
  db.session.add(hotel)

  # Save spacy vocab
  review = reviews.iloc[0]
  if "spacy_text" in review:
    vocab = review["spacy_text"][0].vocab
    vocab.to_disk(os.path.join(app.config["STORAGE_PATH"],
                               "vocab_{}".format(hotel_id)))

  # Add reviews to database
  unigrams = {}
  for _, review in reviews.iterrows():
    review_obj = models.Review.from_series(review, hotel_id)
    # Add sentences to database
    sentences, unigrams = review_obj.create_sentences(unigrams)
    db.session.add(review_obj)
    #for sentence in sentences:
    #  db.session.add(sentence)
    # Add unigrams to database
    for unigram in unigrams.values():
      db.session.add(unigram)

  db.session.commit()
  return flask.redirect(flask.url_for("analysis", hotelname=hotelname))


@app.route("/analysis/<hotel_id>?word=<word>")
@app.route("/analysis/<hotel_id>")
def analysis(hotel_id: str, word: Optional[str] = None):
  """Generates the analysis page (with aspects and visualizations).

  Args:
    hotel_id: The hotel id which is the name of the folder that contains
      hotel's data in the STORAGE PATH.
    word: A word aspect for generating the corresponding reviews page.
      See `word_mode` description in `view_reviews` for more details.
  """
  # TODO: Implement word merging
  hotel = models.Hotel.query.get(hotel_id)
  if word is not None:
    unigram = models.Unigram.query.get(word)
    return flask.render_template("reviews.html", hotel=hotel, unigram=unigram)
    #return view_reviews(word, hotel)
  return flask.render_template("analysis.html", hotel=hotel,
                               n_aspects=app.config["NUM_ASPECTS"])


@app.route('/', methods=["GET", "POST"])
def main():
  """Generates main page with available hotels and options to add more."""
  if flask.request.method == "POST":
    if flask.request.form:
      if "maxpages" in flask.request.form:
        max_review_pages = flask.request.form["maxpages"]
      else:
        max_review_pages = None

      if max_review_pages is not None:
        if not max_review_pages.isdigit():
          raise ValueError("Number of review pages should be an integer "
                           "but {} was given.".format(max_review_pages))
        max_review_pages = int(max_review_pages)

      raise NotImplementedError
      #return scrape(flask.request.form["tripadvlink"], max_pages=max_review_pages)

    if flask.request.files:
      return upload_zip(flask.request.files["data"])

  return flask.render_template("home.html", hotels=models.Hotel.query.all())
