import argparse
from scraping import scraper


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--url', type=str)
  parser.add_argument('--save-dir', type=str, default="/home/stavros/DATA/")
  parser.add_argument('--max-reviews', type=int, default=None)

  args = parser.parse_args()
  url = args.url

  # Add {} after Reviews
  n = url.find("Reviews") + len("Reviews")
  url = "".join([url[:n], "{}", url[n:]])
  print("Given url:")
  print(url)
  print()

  ta_scraper = scraper.TripAdvisorScraper(url)
  ta_scraper.scrape_reviews(max_reviews=args.max_reviews)
  ta_scraper.save(args.save_dir)
