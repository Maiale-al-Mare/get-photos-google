from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup as Bs4
import requests
import shutil
import base64
import time
import os
import re

response = None

keyword = input('Qual è la parola chiave? ').strip()

scroll_to_bottom_number = input('Quante volte vuoi che il browser scorra a fine pagina?\nConta che una pagina sola può '
                                'contenere più di cento foto. Default: 1 ').strip()

if scroll_to_bottom_number.isnumeric():
    if scroll_to_bottom_number != '0':
        scroll_to_bottom_number = int(scroll_to_bottom_number)
    else:
        print('Non posso non scorrere in basso, quindi lo farò una volta')
        scroll_to_bottom_number = 1
elif scroll_to_bottom_number == '':
    scroll_to_bottom_number = 1
else:
    print('Devi rispondere con un numero')
    exit(0)

chrome = Chrome()
chrome.maximize_window()


def main():
    global response
    photo_dir_name = keyword.replace(' ', '-') + '-photos'
    chrome.get(f'https://www.google.com/imghp?hl=en&q={keyword}')
    chrome.find_element_by_css_selector('input[name=q]').send_keys(Keys.ENTER)
    scroll_pause_time = 0.10
    scroll_length = 200
    scroll_position = 0
    for _ in range(scroll_to_bottom_number):
        time.sleep(1.5)
        page_height = int(chrome.execute_script('return document.body.scrollHeight'))
        while scroll_position < page_height:
            scroll_position = scroll_position + scroll_length
            chrome.execute_script('window.scrollTo(0, ' + str(scroll_position) + ');')
            time.sleep(scroll_pause_time)
        time.sleep(1.5)
    source = chrome.page_source
    chrome.close()
    soup = Bs4(source, 'html.parser')
    photos = [photo for photo in soup.find(attrs={'id': 'islmp'}).find_all('img')]
    if not os.path.exists(photo_dir_name):
        os.mkdir(photo_dir_name)
    os.chdir(photo_dir_name)
    with open('sources.txt', 'a') as sources:
        for x, photo in enumerate(photos):
            try:
                key = 'src' if 'src' in photo.attrs else 'data-src'
                if photo[key].startswith('data'):
                    mime_type = re.search(':(.+);', photo[key]).group(1).split('/')[1]
                else:
                    sources.write(photo[key] + '\n')
                    response = requests.get(photo[key], stream=True)
                    if not response.ok:
                        continue
                    mime_type = response.headers['content-type'].split('/')[1]
                with open(f'{keyword.replace(" ", "-")}-{x}.{mime_type}', 'wb') as handle:
                    if photo[key].startswith('data'):
                        handle.write(base64.decodebytes(photo[key].split('base64,')[1].encode('unicode_escape')))
                    else:
                        for block in response.iter_content(1024):
                            if not block:
                                break
                            handle.write(block)
            except Exception as e2:
                print(f'C\'è stato un errore: {e2}')
                continue
    os.chdir('..')
    shutil.make_archive(photo_dir_name, 'zip', photo_dir_name)
    shutil.rmtree(photo_dir_name)
    print('Fatto!')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Terminato')
    except Exception as e:
        print(f'C\'è stato un errore: {e}')
