"""
This code will fetch data form the google images and save the data to scrapped folder.

For this, apart form python you should have some knowledge of html.
"""

import requests
from bs4 import BeautifulSoup
import os

def fetch_and_download(search):
    try:
        # Preparing the web url to fetch the data.
        # in our case the url should looks like: 
        # https://www.google.com/search?q=dog&sxsrf=ALiCzsZ3fBRElRdo57sDCM9KCbB1W8n1NQ:1672939134414&source=lnms&tbm=isch&sa=X&ved=2ahUKEwierdn297D8AhWRr1YBHY8lDFkQ_AUoAXoECAEQAw&biw=1536&bih=763&dpr=1.25
        web_url = f"https://www.google.com/search?q={search.strip().replace(' ', '+')}" \
                    f"&sxsrf=ALiCzsZ3fBRElRdo57sDCM9KCbB1W8n1NQ:1672939134414&source=lnms&tbm=isch&sa=X&ved=" \
                    f"2ahUKEwierdn297D8AhWRr1YBHY8lDFkQ_AUoAXoECAEQAw&biw=1536&bih=763&dpr=1.25"
        
        # this line of code will request the data from above url.
        response = requests.get(web_url)

        # For now the data we get from the request is not usable
        # BeautifulSoup library help us to parse the data into a html format
        # from which we can use class and id to fetch the required data.
        supe = BeautifulSoup(response.content, 'html.parser')
        count = 1

        # Make a scrapped folder if not available in the device
        if not 'scrapped' in os.listdir():
            os.mkdir('scrapped')

        # this code will fetch the images one by one and save it to the above folder
        for img in supe.findAll('img'):
            search_url = img.get('src')
            if search_url != None and search_url.startswith('http'):
                name = 'scrapped/'+search+str(count)+'.jpeg'
                img_response = requests.get(img.get('src'))
                with open(name, 'wb') as image:
                    image.write(img_response.content)
                count+=1
    except Exception as e:
        return print(e)

if __name__ == '__main__':
    fetch_and_download('dog')