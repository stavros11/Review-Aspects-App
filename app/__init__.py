import flask
import flask_sqlalchemy
import flask_migrate


# Define app
app = flask.Flask(__name__)
# Storage directory
app.config["STORAGE_PATH"] = "/home/stavros/DATA/TripAdvisorReviews/app_storage"
# Configure SQL SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////home/stavros/DATA/TripAdvisorReviews/app_storage/app.db"
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


def upload_zip(file: werkzeug.datastructures.FileStorage):
  file_path = os.path.join(app.config["STORAGE_PATH"], file.filename)
  file.save(file_path)
  hotel_path = utils.unzip(file_path)
  hotel = models.Hotel.load_from_folder(hotel_path)
  db.session.add(hotel)
  db.session.commit()
  return flask.redirect(flask.url_for("main"))
  #return flask.redirect(flask.url_for("analysis", hotelname=hotel.id))


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
