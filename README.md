# Finding opinions in hotel reviews

This is a simple Flask (web)-app that performs aspect-based opinion mining on Trip Advisor hotel reviews. The app consists of three functionalities:

1. Scrapes reviews for a particular hotel given the URL of its main page on Trip Advisor.
2. Identifies aspects and their sentiment in each review, using [spaCy's](https://github.com/explosion/spaCy) dependency parser and an [opinion lexicon](https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html).
3. Collects aspects and generates a summary page with the most positive and negative aspects of the hotel.

The method and code for identifying aspects is inspired by Peter Min's amazing [Medium article](https://medium.com/@pmin91/aspect-based-opinion-mining-nlp-with-python-a53eb4752800) and the relevant [code](https://github.com/pmin91/DS_projects). 

Identifying aspects in customer reviews is an interesting branch of NLP that allows to extract information beyond simple star ratings (which are known to be subjective and focused on very specific categories). The results from such analysis could be useful both for the management by identifying:
  * weak aspects that need improvement
  * strong aspects to use in advertisement.
  
but also for customers, who could check how a hotel performs in aspects they find important. Furthermore the methods are applicable to any area with abundance of customer reviews (restaurants, products, etc.).

## Depedencies

 * `pandas`, `plotly`.
 * `requests`, `bs4` for scraping.
 * `spaCy` with an English model for identifying aspects.
 * `flask` for app deployment.
 
## Main usage

### Main page

![mainpage](https://github.com/stavros11/Review-Aspects-App/blob/e88a3de4069d5e013cc524a259c9ad981ebd2b42/screenshots/homepage.png?raw=true)

When running the app locally, all scraped hotel data are saved in a local static path (`STORAGE_PATH`). The available hotels that already exist there will appear in the main page. It is possible to add a new hotel in two different ways:
 
 1. By providing a Trip Advisor URL to scrape and analyze from scratch.
 2. By uploading the data of a previously scraped hotel (for example from a different directory or a different computer).
 
### Hotel analysis page

![analysispage](https://github.com/stavros11/Review-Aspects-App/blob/45002dc995708404eef5726cf9b92d0bc29b7116/screenshots/analysispage.png?raw=true)

Clicking to a specific hotel redirects to a page with its most common positive and negative aspects. Each aspect word is mapped three numbers:
  1. The overal sentiment score (**TODO:** Add details on how this is calculated).
  2. The number of reviews that the word appears as a *positive* aspect.
  3. The number of reviews that the word appears as a *negative* aspect.
  
Words are sorted according to sentiment score (most positive / most negative).

The analysis page also contains simple visualizations:
  * Pie chart with the hotel star ratings (1-5) as scraped from Trip Advisor.
  * Pie chart with the sentiment of reviews from our aspect analysis.
  * Bar chart with category star ratings (1-5) as scraped from Trip Advisor.
  
#### Reviews that contain an identified aspect

![reviewpage](https://github.com/stavros11/Review-Aspects-App/blob/45002dc995708404eef5726cf9b92d0bc29b7116/screenshots/reviewpage.png?raw=true)

Clicking on a specific aspect word gives all the reviews for which this word was identified as an aspect. The word is shown in bold and other aspect words in the same review are highlighted as green/red for positive/negative sentiment score. This allows to check exactly what people are saying about the selected aspect!

*Bonus feature:* Clicking in the review title redirects to the review on Trip Advisor's website.

## Disclaimer

The app was developed in my free time, is not used for profit and is not related to any professional project. I am not affiliated with the hotels mentioned in the above screenshots, except Stavros Melathron Studios which is owned by my parents and gave me the idea for this project (so I thought of giving back some credit!). The other hotels are used for demonstration puproses and I do not intend to advertise or criticize them. I am not affiliated with Trip Advisor and all scraped data are publicly accessible.

The aspect identification was (mostly) taken from [Peter Min's repo](https://github.com/pmin91/DS_projects). The rest functionality (scraping, aspect collection and flask deployment) was developed by myself following various online guides and videos.
