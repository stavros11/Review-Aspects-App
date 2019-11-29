"""Hardcoded directories to import when needed."""
import os

#base = "/home/stavros/DATA"
base = "D:/"

#opinion_lexicon = "/home/stavros/GitHub/Text-Classification/opinion-lexicon"
opinion_lexicon = "C:/Users/SU/Documents/GitHub/Text-Classification"


airbnb = os.path.join(base, "AirbnbReviews")
trip_advisor = os.path.join(base, "TripAdvisorReviews")
google_word2vec = os.path.join(base, "GoogleNews-vectors-negative300.bin.gz")


hotel_order = ["rodos_palace", "sentido_ixian_grand", "kresten_royal", "titania_hotel"]#, "lindian_village"

hotel_db = {#"lindian_village": "lindian_village_654reviews_withaspects",
            "kresten_royal": "the_kresten_royal_villas_1747reviews_withaspects",
            "sentido_ixian_grand": "sentido_ixian_grand_1235reviews_withaspects",
            "rodos_palace": "rodos_palace_1280reviews_withaspects",
            "titania_hotel": "titania_hotel_934reviews_withaspects"}

# "stavros_melathron": "stavros_melathron_studios_115reviews_withaspects"