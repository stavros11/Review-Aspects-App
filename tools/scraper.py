import os
import requests
import bs4
import json
import pandas as pd
from typing import Dict, List, Optional, Union


def find_reviews_dict(root, target="mgmtResponse") -> Optional[str]:
  """Helper method that finds the dictionary key path of reviews in JS code."""
  traces = [""]
  stack = [root]
  while stack:
    node = stack.pop()
    trace = traces.pop()
    if isinstance(node, dict):
      if target in node:
        return "/".join([trace, target])
      for k, v in node.items():
        traces.append("/".join([trace, k]))
        stack.append(v)
    elif isinstance(node, list):
      for i, v in enumerate(node):
        traces.append("/".join([trace, "__LS__{}".format(i)]))
        stack.append(v)
    elif isinstance(node, str):
      if target in node:
        return trace
  return None


def multiple_dict_indexing(d: Union[Dict, List], ids: List[str],
                           list_token="__LS__") -> Union[Dict, List]:
  if ids[0][:len(list_token)] == list_token:
    new_d = d[int(ids[0][len(list_token):])]
  else:
    new_d =d[ids[0]]

  if len(ids) > 1:
    return multiple_dict_indexing(new_d, ids[1:])
  return new_d


class TripAdvisorScraper:

  _REVIEW_DATA = ["id", "absoluteUrl", "createdDate", "publishedDate",
                  "locationId", "originalLanguage", "language",
                  "tripInfo/stayDate", "tripInfo/tripType",
                  "helpfulVotes", "title", "text",
                  "rating", "additionalRatings"]

  _REVIEWER_DATA = ["username", "userProfile/userId",
                    "userProfile/hometown/locationId",
                    "userProfile/hometown/location/additionalNames/long"]

  # mgmtResponse/
  _RESPONSE_DATA = ["id", "publishedDate", "language",
                    "username", "connectionToSubject", "text"]

  _REVIEW_TITLES = ([x.split("/")[-1] for x in _REVIEW_DATA] +
                    ["username", "userId", "user_hometownId", "user_hometownName"] +
                    ["response_{}".format(x) for x in _RESPONSE_DATA])

  _SCRIPT_TARGET = "window.__WEB_CONTEXT__"

  def __init__(self, base_url: str, reviews_per_page: int = 5):
    self.session = requests.Session()
    self.reviews = []

    self.n_reviews = None
    self.reviews_per_page = reviews_per_page
    self.url = base_url

    self.data = self.scrape_data(self.url.format(""))
    print("Found {} reviews for {}.".format(self.n_reviews, self.data["name"]))

  def scrape_data(self, url: str) -> Dict:
    soup = self.get_soup(url)
    base = self.get_base(soup)
    data = {"locationId": base["locationId"],
            "name": base["name"],
            "accommodationCategory": base["accommodationCategory"],
            "ratingCounts": base["reviewAggregations"]["ratingCounts"],
            "languageCounts": base["reviewAggregations"]["languageCounts"],
            "absoluteUrl": url}
    try:
      data["additionalRatings"] = self.find_additional_ratings(soup)
    except AssertionError:
      print("Failed to scrape additional ratings.")
    return data

  def scrape_reviews(self, start_page: int = 0, max_reviews: Optional[int] = None):
    counter = start_page * self.reviews_per_page
    if max_reviews is None: max_reviews = self.n_reviews

    while counter < max_reviews:
      url = self._get_url(counter)
      page_nr = counter // self.reviews_per_page + 1
      try:
        soup = self.get_soup(url)
        revlist = self.get_base(soup)["reviewListPage"]["reviews"]
        for review in revlist:
          self.reviews.append(self.scrape_review(review))
        print("Page {} - {} reviews scrapped.".format(page_nr, len(revlist)))
      except Exception:
        print("Failed to read reviews on page {}.".format(page_nr))

      counter += self.reviews_per_page

  def get_soup(self, url: str) -> bs4.BeautifulSoup:
    req = self.session.get(url)
    assert req.status_code == 200
    return bs4.BeautifulSoup(req.text, "html.parser")

  def get_base(self, soup: bs4.BeautifulSoup) -> Dict:
    n = len(self._SCRIPT_TARGET)
    scripts = [script for script in soup.find_all('script')
               if script.text[:n] == self._SCRIPT_TARGET]
    assert len(scripts) == 1

    script_dict = json.loads(scripts[0].text[n + 15:-2])
    #base = script_dict["apolloCache"][0]["result"]["locations"][0]

    base_path = find_reviews_dict(script_dict)
    base_path = base_path.split("/")[1:]
    final_idx = base_path.index("reviewListPage")
    base = multiple_dict_indexing(script_dict, base_path[:final_idx])

    # Example path
    #/435984507/data/locations/0/reviewListPage/reviews/4/mgmtResponse
    if "reviewListPage" in base and "totalCount" in base["reviewListPage"]:
      if self.n_reviews is None:
        self.n_reviews = base["reviewListPage"]["totalCount"]
      else:
        assert self.n_reviews == base["reviewListPage"]["totalCount"]

    return base

  def find_additional_ratings(self, soup: bs4.BeautifulSoup) -> Dict:
    _class_name = "hotels-hotel-review-about-with-photos-Reviews__subratingRow--2u0CJ"
    ratings_list = soup.find_all("div", {"class": _class_name})
    ratings = {}
    for rating in ratings_list:
      score_bubble = rating.find("span")["class"]
      assert len(score_bubble) == 2
      assert score_bubble[0] == "ui_bubble_rating"
      score = float(score_bubble[1].split("_")[-1]) / 10.0
      ratings[rating.text] = score
    return ratings

  def _get_url(self, counter: int) -> str:
    if counter > 0:
      return "".join([self.url.format("-or{}".format(counter)), "#REVIEWS"])
    return self.url.format("")

  def scrape_review(self, review: Dict) -> List:
    data = [self._nested_get(review, k.split("/")) for k in self._REVIEW_DATA[:-1]]
    # Pay attention to how you log additional ratings
    add_ratings = self._nested_get(review, [self._REVIEW_DATA[-1]])
    # add_ratings is a List of Dicts
    data.append({r["ratingLabel"]: r["rating"] for r in add_ratings})

    for k in self._REVIEWER_DATA:
      data.append(self._nested_get(review, k.split("/")))

    for k in self._RESPONSE_DATA:
      actual_k = "mgmtResponse/{}".format(k)
      data.append(self._nested_get(review, actual_k.split("/")))

    return data

  def _nested_get(self, data: Dict, keys: List[str]):
    if not (isinstance(data, dict) and keys[0] in data):
      return None

    if len(keys) > 1:
      return self._nested_get(data[keys[0]], keys[1:])
    return data[keys[0]]

  @property
  def lower_name(self) -> str:
    return "_".join(self.data["name"].lower().split(" "))

  def to_dataframe(self) -> pd.DataFrame:
    return pd.DataFrame(self.reviews, columns=self._REVIEW_TITLES)

  def save(self, folder: str):
    folder_name = os.path.join(folder, self.lower_name)
    if os.path.isdir(folder_name):
      raise FileExistsError("Folder {} already exists in storage.".format(
          folder_name))

    os.mkdir(folder_name)
    txt_name = os.path.join(folder_name, "{}_meta.txt".format(self.lower_name))
    csv_name = os.path.join(folder_name, "{}_{}reviews.csv".format(
        self.lower_name, self.n_reviews))
    with open(txt_name, "w") as file:
      json.dump(self.data, file)
    df = self.to_dataframe()
    df.to_csv(csv_name, index=False)