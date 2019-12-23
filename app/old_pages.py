def scrape(url: str, max_pages: Optional[int] = None):
  """Scrapes a hotel from Trip Advisor and generates its analysis page.

  Args:
    url: URL of the Trip Advisor main page of the hotel.
    max_pages: Maximum number of review pages to scrape.
      If None all available reviews are scraped. It is advisable to use a small
      number for testing because spaCy may take some time to run and we do not
      have a nice loading screen implemented yet.
  """
  import scraping
  import nlptools
  # TODO: Fix case where we already have data for the given URL
  # (currently this should give an error)

  # Add {} url to access review pages
  n = url.find("Reviews") + len("Reviews")
  url = "".join([url[:n], "{}", url[n:]])
  # Scrape reviews
  scraper = scraping.scraper.TripAdvisorScraper(url)
  # FIXME: Fix the scraper to take max_pages instead of max_reviews as Trip
  # Advisor may change in the future and no longer have 5 reviews per page
  scraper.scrape_reviews(max_reviews=max_pages * 5)
  scraper.save(app.config["STORAGE_PATH"])
  # Find aspects
  nlptools.aspects.find_aspects(scraper.csv_path)
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


def view_reviews(word: str, hotel: tools.hotel.Hotel):
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
  color = tools.containers.get_color(True) # FIXME: Fix color
  sentences = hotel.unigrams.sentences[word]
  return flask.render_template("reviews.html", hotel=hotel, sentences=sentences,
                               word=word, color=color)
