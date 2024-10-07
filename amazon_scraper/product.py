import json

class Product():
    """ Hold information about object of type Product
    """
    def __init__(self, url='', asin='', title='', brand='', description='', price=None, img_url='', rating_stars='', review_count=None, bestseller=False, prime=False):

        self.url = url
        self.asin = asin
        self.title = title
        self.brand = brand
        self.description = description
        self.price = price
        self.img_url = img_url
        self.rating_stars = rating_stars
        self.review_count = review_count
        self.bestseller = bestseller
        self.prime = prime
    
    def to_json(self):
        """convert object to json string format
        """
        return json.dumps(self, default=lambda o: o.__dict__)
    
