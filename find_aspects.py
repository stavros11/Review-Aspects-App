import argparse
from nlptools import aspects


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--csv-path', type=str, default="")
  args = parser.parse_args()

  aspects.find_aspects(args.csv_path)
