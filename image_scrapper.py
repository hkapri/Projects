import requests
from bs4 import BeautifulSoup
import shutil
import random
import os
from datetime import datetime, timedelta

def fetch_and_download(search):
    process = dict()
    try:
        web_url = f"https://www.google.com/search?q={search.strip().replace(' ', '+')}" \
                    f"&sxsrf=ALiCzsZ3fBRElRdo57sDCM9KCbB1W8n1NQ:1672939134414&source=lnms&tbm=isch&sa=X&ved=" \
                    f"2ahUKEwierdn297D8AhWRr1YBHY8lDFkQ_AUoAXoECAEQAw&biw=1536&bih=763&dpr=1.25"
        response = requests.get(web_url)
        supe = BeautifulSoup(response.content, 'html.parser')
        count = 1
        images_data = []
        if not 'scrapped' in os.listdir():
            os.mkdir('scrapped')
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