"""Hardcoded directories to import when needed."""
import os


airbnb = "/home/stavros/DATA/AirbnbReviews"
trip_advisor = "/home/stavros/DATA/TripAdvisorReviews"
google_word2vec = "/home/stavros/DATA/GoogleNews-vectors-negative300.bin.gz"


hotel_urls = {"Lindian Village": "lindian_village",
              "Stavros Melathron": "stavros_melathron",
              "Kresten Royal": "kresten_royal"}

hotel_db = {"lindian_village": "lindian_village_654reviews_withaspects",
            "stavros_melathron": "stavros_melathron_studios_115reviews_withaspects",
            "kresten_royal": "the_kresten_royal_villas_1747reviews_withaspects"}


def hotel_part_dir(hotel_name: str) -> str:
  assert hotel_name in hotel_db
  return os.path.join(hotel_name, hotel_db[hotel_name])


def hotel_full_dir(hotel_name: str) -> str:
  return os.path.join(trip_advisor, hotel_part_dir(hotel_name))