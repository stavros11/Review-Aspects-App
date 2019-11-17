import os
import argparse
from aspects import containers
from utils import directories
from typing import Optional


def main(filename: str, cut_off: Optional[float] = None, plot: bool = False,
         start: int = 0, end: int = 20):
  data_dir = os.path.join(directories.trip_advisor, filename)

  aspects = containers.DataAspects.load(data_dir)

  if cut_off is not None:
    aspects.merge(cut_off=0.4)
    container = aspects.merged_container
  else:
    container = aspects.container

  if plot:
    fig = container.get_figure(start=start, end=end)
    fig.show()

  else:
    print(container.common_positive(start, end))
    print("\n")
    print(container.common_negative(start, end))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--filename", type=str)
  parser.add_argument("--plot", action="store_true")
  parser.add_argument("--cut-off", type=float, default=None)
  parser.add_argument("--start", type=int, default=0)
  parser.add_argument("--end", type=int, default=20)

  args = parser.parse_args()
  main(**vars(args))