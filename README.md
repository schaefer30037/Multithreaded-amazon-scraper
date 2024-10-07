# Multithreaded-amazon-scraper

# Description
Improved on existing code: [https://github.com/ankushduacodes/Multithreaded-amazon-scraper/tree/master/amazon_scraper](https://github.com/ankushduacodes/Multithreaded-amazon-scraper)

This package allows you to search and scrape for products on [Amazon](https://www.amazon.com) and extract some useful information (price, ratings, number of comments).

# Requirements
- Python 3
- pip3

# Dependencies
```bash
pip install -r requirements.txt
```

# Usage
1. Clone this repo or zip download it.
2. Open a terminal or cmd at download folder directory
3. run:
```bash 
python example.py -w "<word you want to search>"
```
4. Above step with create a .json file(in same directory as example.py) with the products that were found.
5. For more help just run:
```bash 
python example.py --help
```
If these don't work, try pip3 and python3

### Information fetched

Attribute name      | Description
------------------- | ---------------------------------------
url                 | Product URL
title               | Product title
brand               | Product brand
description         | Product description
price               | Product price
rating              | Rating of the products
review_count        | Number of customer reviews
img_url             | Image URL
bestseller          | Tells whether a product is best seller or not
prime               | Tells if product is supported by Amazon prime or not
asin                | Product ASIN ([Amazon Standard Identification Number](https://fr.wikipedia.org/wiki/Amazon_Standard_Identification_Number))

### Output Format
Output is provided in the from of a json file, please refer to the [products.json](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/products.json) as an example file which was produced with search word 'toaster'

# Design Decisions
1. scraper.py, In method [get_page_content](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/amazon_scraper_module/scraper.py#L102), retries were added to make a valid connection with amazon servers even if it connection request was denied.

2. function -> [get_request](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/amazon_scraper_module/scraper.py#L56), returns None when requests.exceptions.ConnectionError occurs and ripples its way down to calling functions to terminate the thread normally instead of abruptly calling sys.exit() which surely will kill the thread but if the thread being killed holds GIL component, in that case it will lead to [Deadlock](https://en.wikipedia.org/wiki/Deadlock).

3. function -> [get_page_content](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/amazon_scraper_module/scraper.py#L102), if no valid page was found even after retries it returns None in addition to returning None for Nonetype response from get_request.

4. Decision number 2 and 3 were made keeping in mind that in a multithreaded program, multiple threads are working simultaneously, while doing that there may be a case where 1 or 2 out of 10 or 20 threads does not get valid response (Please check [check_page_validity](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/amazon_scraper_module/scraper.py#L83[) and [get_request](https://github.com/ankushduacodes/amazon-search-scraper/blob/master/amazon_scraper_module/scraper.py#L56) function for documentation and more), then we terminate only those threads safely while others work to produce the valid output.

# Performance Benchmark
On my network connection (results may vary depending on your connection speed)

Number of pages     | Number of products | Time              |
--------------------|--------------------|-------------------|
 1                  | 22                 | 90  s             |
 5                  | 110                | 7.5 min           |
--------------------------------------------------------------

## Future Imporvements
- [ ] Update benchmarking
- [ ] Handle a variety of products. Book product data is incomplete
- [ ] Handle Amazon-owned brands. Brand is left blank in these cases
