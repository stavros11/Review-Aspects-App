import flask
from application import pages


app = flask.Flask(__name__)

@app.route("/<hotelname>?word=<word>")
@app.route("/<hotelname>")
@app.route('/')
def main(hotelname=None, word=None):
  if hotelname is None:
    return pages.hotels_page()
  return pages.analysis_page(hotelname, word)


if __name__ == "__main__":
  app.run(debug=True)