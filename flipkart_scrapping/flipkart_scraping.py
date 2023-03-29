"""
This code will fetch data form the flipkart website.

For this, apart form python you should have some knowledge of html.
"""

import requests
from bs4 import BeautifulSoup

def flipkart_product_scrap(product_name):
    """
    This method will scrap the below details form the flipkart website.
    price, average rating, variants, highlights, number of ratings, image
    """
    try:
        # Preparing the web url with the product details
        # in our case the url should look like : https://www.flipkart.com/search?q=iphone+14+pro+max'
        web_url = f"https://www.flipkart.com/search?q={product_name.strip().replace(' ', '+')}"

        # this line of code will request the data from above url.
        response = requests.get(web_url)

        # Checking, if the request is success or not
        # if not, process will return False
        if response.status_code != 200:
            return False

        # For now the data we get from the request is not usable
        # BeautifulSoup library help us to parse the data into a html format
        # from which we can use class and id to fetch the required data.
        beautify_data = BeautifulSoup(response.content, 'html.parser')

        # Flipkart use two differnt format to display different type of products.
        # The below code will check the both class to find the accurate data.
        all_products = beautify_data.findAll(class_='_1fQZEK')
        if not all_products:
            all_products = beautify_data.findAll(class_='_2rpwqI')
        
        # get the first product in the list and will fetch data for that product
        # Like we click on the first product in the flipkart website
        # which will display all the specifications of that product.
        # The difference is that we are doing it from code.
        product_ref = all_products[0]['href']
        response = requests.get(f'https://www.flipkart.com{product_ref}')
        if response.status_code != 200:
            return False
        beautify_product = BeautifulSoup(response.content, 'html.parser')

        # Fetching the required data of the product.
        price = beautify_product.find(class_='_30jeq3').text
        avg_rating = beautify_product.find(class_='_1lRcqv').next_element.text
        num_rating = beautify_product.find(class_='_1lRcqv').nextSibling.text
        varients = []
        for varient in beautify_product.findAll(class_='_22QfJJ'):
            attrib = varient.next_element.text
            vars = []
            for var in varient.next_element.nextSibling.next_element.contents:
                vars.append(var.text)
            varients.append({attrib: ', '.join(vars)})
        highlights = []
        for highlight in beautify_product.findAll(class_='_21Ahn-'):
            highlights.append(highlight.text)
        img_link = beautify_product.findAll(class_='q6DClP')[0]['src'].replace('128', '416')
        prd_name = beautify_product.find(class_='B_NuCI').text

        # return the Data prepared
        return {'price': price,
                'average_rating': avg_rating,
                'num_rate': num_rating,
                'varients': varients,
                'highlights': highlights,
                'img_link': img_link,
                'name': prd_name}
    except Exception as e:
        return False


if __name__ == '__main__':
    scrapped_data = flipkart_product_scrap('iphone 14 pro max')
    if scrapped_data:
        for key, value in scrapped_data.items():
            print(f"{key} : {value}")
    else:
        print('something went wrong!!')