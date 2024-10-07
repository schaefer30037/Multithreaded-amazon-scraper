# -*- coding: utf-8 -*-
"""
Module to get and parse the product info on Amazon Search
"""

import re
import time
import random
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from .product import Product


base_url = "https://www.amazon.com"


class Scraper():
    """Does the requests with the Amazon servers
    """

    def __init__(self, word):
        """ Init of the scraper
        """
        self.item_count = 1
        self.word = word
        self.session = requests.Session()
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            # 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
            # Add more user agents here
        ]
        self.headers = {
            'authority': 'www.amazon.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': random.choice(user_agents),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        self.product_obj_list = []
        self.page_list = []

    def prepare_url(self, search_word):
        """Get the Amazon search URL, based on the keywords passed

        Args:
            search_word (str): word passed by the user to search amazon.com for (eg. smart phones)

        Returns:
            search url: Url where the get request will be passed (it will look something like https://www.amazon.com/s?k=smart+phones)
        """
        return urljoin(base_url, ("/s?k=%s" % (search_word.replace(' ', '+'))))

    def get_request(self, url):
        """ Places GET request with the proper headers

        Args:
            url (str): Url where the get request will be placed

        Raises:
            requests.exceptions.ConnectionError: Raised when there is no internet connection while placing GET request

            requests.HTTPError: Raised when response stattus code is not 200

        Returns:
            response or None: returns whatever response was sent back by the server or returns None if requests.exceptions.ConnectionError occurs
        """
        try:

            # if using scraperapi: www.scraperapi.com 

            API_KEY = "aedb8b557ff49e372f1b2691c14e27b2"
            payload = {"api_key": API_KEY, "url": url}
            response = requests.get("https://api.scraperapi.com", params=payload)
            

            # If not using scraperapi

            # time.sleep(random.randint(1, 15))
            # response = self.session.get(url, headers=self.headers)
            # if response.status_code != 200:
            #     raise requests.HTTPError(
            #         f"Error occured, status code: {response.status_code}")


        except (requests.exceptions.ConnectionError, requests.HTTPError) as e:
            print(str(e) + " while connecting to " + url)
            return None

        return response

    def check_page_validity(self, page_content):
        """Check if the page is a valid result page

        Returns:
            valid_page: returns true for valid page and false for invalid page(in accordance with conditions)
        """

        if "We're sorry. The Web address you entered is not a functioning page on our site." in page_content:
            valid_page = False
            print("Amazon: We're sorry. The Web address you entered is not a functioning page on our site.")
        elif "Try checking your spelling or use more general terms" in page_content:
            valid_page = False
            print("Amazon: Try checking your spelling or use more general terms")
        elif "Sorry, we just need to make sure you're not a robot." in page_content:
            valid_page = False
            print("Amazon: Sorry, we just need to make sure you're not a robot.")
        elif "The request could not be satisfied" in page_content:
            valid_page = False
            print("Amazon: The request could not be satisfied")
        else:
            valid_page = True
        return valid_page

    def get_page_content(self, search_url):
        """Retrieve the html content at search_url

        Args:
            search_url (str): Url where the get request will be placed

        Raises:
            ValueError: raised if no valid page is found

        Returns:
            response.text or None: returns html response encoded in unicode or returns None if get_requests function or if the page is not valid even after retries
        """

        valid_page = True
        trial = 0
        # if a page does not get a valid response it retries(5 times)
        max_retries = 5
        while (trial < max_retries):

            response = self.get_request(search_url)

            if (not response):
                return None

            valid_page = self.check_page_validity(response.text)

            if valid_page:
                break

            print("No valid page was found, retrying in 30 seconds...")
            time.sleep(30)
            trial += 1

        if not valid_page:
            print(
                "Even after retrying, no valid page was found on this thread, terminating thread...")
            self.generate_output_file()
            return None

        return response.text

    def get_product_url(self, product):
        """Retrieves and returns product url

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            url: returns full url of product
        """

        # regexp = "a-link-normal a-text-normal".replace(' ', '\s+')
        regexp = "a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal".replace(' ', '\s+')
        classes = re.compile(regexp)
        product_url = product.find('a', attrs={'class': classes}).get('href')
        return base_url + product_url

    def get_product_asin(self, product):
        """ Retrieves and returns Amazon Standard Identification Number (asin) of a product

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            asin: returns Amazon Standard Identification Number (asin) of a product
        """

        return product.get('data-asin')

    def get_brand_and_description(self, url):
        """Retrieves and returns brand, description
        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            title: returns brand, description or empty string if they aren't found
        """
        try:
            # time.sleep(15)
            page_content = self.get_page_content(url)
            if not page_content:
                return '', ''
            soup = BeautifulSoup(page_content, "html5lib")
            
            # Get brand
            brand_row = soup.find('tr', class_='po-brand')
            if brand_row:
                brand = brand_row.find_all('td')[1].find('span').text.strip()
            else:
                brand_link = soup.find('a', id='bylineInfo')
                if brand_link:
                    brand_text = brand_link.get_text()
                    # Split the text to get the brand name
                    brand = brand_text.split(': ')[1] if ': ' in brand_text else brand_text
                else:
                    brand = ''
            
            # Get description
            about_section = soup.find(re.compile(r'^h[1-6]$'), text=re.compile(r"About\s+this\s+item"))

            if about_section:
                parent_div = about_section.find_parent('div')
                feature_items = parent_div.find_all('li')
                description = [li.get_text(strip=True) for li in feature_items]

            else:
                feature_bullets = soup.find('div', id='feature-bullets')
                if feature_bullets:
                    # Extract all list items from the feature bullets section
                    description = [li.get_text(strip=True) for li in feature_bullets.find_all('li')]
                else:
                    description = []

            if not description:
                # print(url)
                with open("product_page.html", "w", encoding="utf-8") as file:
                    file.write(str(soup.prettify()))  # Prettify makes the HTML easier to read
                    file.write("\n\n")

            return brand, '\n'.join(description)

            # with open("product_page.html", "w", encoding="utf-8") as file:
            #     file.write(str(soup.prettify()))  # Prettify makes the HTML easier to read
            #     file.write("\n\n")
            
            # brand_label = product.find('span', text="Brand")

            # # Once 'Brand' is found, locate the next 'span' with class 'a-text-bold' that contains the actual brand
            # brand = brand_label.find_next('span', class_='a-text-bold')
            # return brand.text.strip()
        
        except AttributeError:
            """AttributeError occurs when no brand is found and we get back None
            in that case when we try to do title.text it raises AttributeError
            because Nonetype object does not have text attribute"""
            return ''
        
    def get_product_title(self, product):
        """Retrieves and returns product title
        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            title: returns product title or empty string if no title is found
        """

        regexp = "a-color-base a-text-normal".replace(' ', '\s+')
        classes = re.compile(regexp)
        try:
            title = product.find('span', attrs={'class': classes})
            return title.text.strip()

        except AttributeError:
            """AttributeError occurs when no title is found and we get back None
            in that case when we try to do title.text it raises AttributeError
            because Nonetype object does not have text attribute"""
            return ''

    def get_product_price(self, product):
        """Retrieves and returns product price
        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            price: returns product price or None if no price is found
        """

        try:
            price = product.find('span', attrs={'class': 'a-offscreen'})
            return float(price.text.strip('$').replace(',', ''))

        except (AttributeError, ValueError):
            """AttributeError occurs when no price is found and we get back None
            in that case when we try to do price.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting price.text.strip() into float
            of that value and that value for some reason is not convertible to
            float"""

            return None

    def get_product_image_url(self, product):
        """Retrieves and returns product image url

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            image_url: returns product image url
        """

        image_tag = product.find('img')
        return image_tag.get('src')

    def get_product_rating(self, product):
        """Retrieves and returns product rating

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            rating : returns product rating or returns None if no rating is found
        """

        try:
            rating = re.search(r'(\d.\d) out of 5', str(product))
            return float(rating.group(1))

        except (AttributeError, ValueError):
            """AttributeError occurs when no rating is found and we get back None
            in that case when we try to do rating.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting rating.group(1) into float
            of that value and that value for some reason is not convertible to
            float"""

            return None

    def get_product_review_count(self, product):
        """Retrieves and returns number of reviews a product has

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            review count: returns number of reviews a product has or returns None if no reviews are available
        """

        try:
            reviews_match = re.search(r'(\d+)\s+ratings', str(product))
    
            if reviews_match:
                return int(reviews_match.group(1).strip().replace(',', ''))
            return None

        except (AttributeError, ValueError):
            """AttributeError occurs when no review_count is found and we get back None
            in that case when we try to do review_count.text it raises AttributeError
            because Nonetype object does not have text attribute"""

            """ValueError is raised while converting review_count.text.strip() into
            int of that value and that value for some reason is not convertible to
            int"""

            return None

    def get_product_bestseller_status(self, product):
        """Retrieves and returns if product is best-seller or not

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            bestseller_status: returns if product is best-seller or not
        """

        try:
            bestseller_status = product.find(
                'span', attrs={'class': 'a-badge-text'})
            return bestseller_status.text.strip() == 'Best Seller'

        except AttributeError:
            """AttributeError occurs when no bestseller_status is found and we get back None
            in that case when we try to do bestseller_status.text it raises AttributeError
            because Nonetype object does not have text attribute
            """
            return False

    def get_product_prime_status(self, product):
        """Retrieves and returns if product is supported by Amazon prime

        Args:
            product (str): higher level html tags of a product containing all the information about a product

        Returns:
            prime_status: eturns if product is supported by Amazon prime
        """

        regexp = "a-icon a-icon-prime a-icon-medium".replace(' ', '\s+')
        classes = re.compile(regexp)
        prime_status = product.find('i', attrs={'class': classes})
        return bool(prime_status)

    def get_product_info(self, product):
        """Gathers all the information about a product and 
        packs it all into an object of class Product
        and appends it to list of Product objects

        Args:
            product (str): higher level html tags of a product containing all the information about a product
        """

        product_obj = Product()
        prod_url = self.get_product_url(product)
        product_obj.url = prod_url
        product_obj.asin = self.get_product_asin(product)
        product_obj.title = self.get_product_title(product)
        product_obj.brand, product_obj.description = self.get_brand_and_description(prod_url)
        product_obj.price = self.get_product_price(product)
        product_obj.img_url = self.get_product_image_url(product)
        product_obj.rating_stars = self.get_product_rating(product)
        product_obj.review_count = self.get_product_review_count(product)
        product_obj.bestseller = self.get_product_bestseller_status(product)
        product_obj.prime = self.get_product_prime_status(product)

        self.product_obj_list.append(product_obj)

    def get_page_count(self, page_content):
        """Extracts number of pages present while searching for user-specified word

        Args:
            page_content (str): unicode encoded response

        Returns:
            page count: returns number of search pages for user-specified word if IndexError is raised then function returns 1
        """

        soup = BeautifulSoup(page_content, 'html5lib')
        try:
            # pagination = soup.find_all(
            #     'li', attrs={'class': ['a-normal', 'a-disabled', 'a-last']})
            # return int(pagination[-2].text)
            
            last_page_span = soup.find('span', class_='s-pagination-item s-pagination-disabled')

            if last_page_span:
                # If the disabled span exists, extract the page number from it
                last_page_number = last_page_span.text.strip()    
            else:
                # If the disabled span doesn't exist, find the largest page number in pagination links
                pagination_links = soup.find_all('a', class_='s-pagination-item s-pagination-button')
                last_page_number = pagination_links[-1].text.strip()
            
            # return min(1, int(last_page_number))
            return int(last_page_number)

        except IndexError:
            return 1

    def prepare_page_list(self, search_url):
        """prepares a url for every page and appends it to page_list in accordance with the page count

        Args:
            search_url (str): url generated by prepare_url function
        """

        for i in range(1, self.page_count + 1):
            self.page_list.append(search_url + '&page=' + str(i))

    def get_products(self, page_content):
        """extracts higher level html tags for each product present while scraping all the pages in page_list

        Args:
            page_content (str): unicode encoded response

        """

        soup = BeautifulSoup(page_content, "html5lib")
        product_list = soup.find_all(
            'div', attrs={'data-component-type': 's-search-result'})
        
        for product in product_list:
            print(f"scraping product {self.item_count}")
            self.get_product_info(product)
            self.item_count += 1
        # product = product_list[0]
        # self.get_product_info(product)
        # with open("product_list.html", "w", encoding="utf-8") as file:
        #     product = product_list[1]
        #     file.write(str(product.prettify()))  # Prettify makes the HTML easier to read
        #     file.write("\n\n")

    def get_products_wrapper(self, page_url):
        """wrapper function that gets contents of a given url and gets products from that url

        Args:
            page_url (str): url of one of search pages
        """

        page_content = self.get_page_content(page_url)
        if (not page_content):
            return

        self.get_products(page_content)

    def generate_output_file(self):
        """generates json file from list of products found in the whole search
        """

        products_json_list = []
        # generate random file name
        filename = self.word + '.json'
        # every object gets converted into json format
        for obj in self.product_obj_list:
            products_json_list.append(obj.to_json())

        products_json_list = ','.join(products_json_list)
        json_data = '[' + products_json_list + ']'
        with open('./' + filename, mode='w') as f:
            f.write(json_data)

    def search(self, search_word):
        """Initializies that search and puts together the whole class

        Args:
            search_word (str): user given word to be searched
        """

        search_url = self.prepare_url(search_word)
        page_content = self.get_page_content(search_url)
        if (not page_content):
            return

        self.page_count = self.get_page_count(page_content)

        """if page count is 1, then there is no need to prepare page list therefore the condition and
        we just parse the content recieved above
        """
        if self.page_count <= 1:
            self.get_products(page_content)

        else:
            # if page count is more than 1, then we prepare a page list and start a thread at each page url
            print(f"Processing {self.page_count} pages")
            self.prepare_page_list(search_url)
            # for page in self.page_list:
            #     print('Processing page:', page)
            #     self.get_products_wrapper(page)
                # time.sleep(120)
            # creating threads at each page in page_list
            with ThreadPoolExecutor() as executor:
                for page in self.page_list:
                    print('processing page ', page)
                    executor.submit(self.get_products_wrapper, page)

        # generate a json output file
        self.generate_output_file()
