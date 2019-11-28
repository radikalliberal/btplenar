import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
from zipfile import ZipFile

def roman_to_int(input_string):
    """ Convert a Roman numeral to an integer. """

    if not isinstance(input_string, type("")):
        raise TypeError("expected string, got %s" % type(input_string))
    input_string = input_string.upper().strip()
    nums = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
    sum = 0
    for i in range(len(input_string)):
        try:
            value = nums[input_string[i]]
            if i + 1 < len(input_string) and nums[input_string[i + 1]] > value:
                sum -= value
            else:
                sum += value
        except KeyError:
            raise ValueError('input_string is not a valid Roman numeral: %s' % input_string)
    return sum

def get_xml(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    filename = url.split('/')[-1]
    if not os.path.exists(os.path.join('./data/', filename)):
        xml_file = requests.get(url, headers=headers)
        open('./data/' + filename, 'wb').write(xml_file.content)

def get_data():
    base_url = 'https://www.bundestag.de'

    if not os.path.exists('./data/MDB_STAMMDATEN.XML'):
        stammdaten = '/resource/blob/472878/7d4d417dbb7f7bd44508b3dc5de08ae2/MdB-Stammdaten-data.zip'
        get_xml(base_url + stammdaten)
        with ZipFile('./data/MdB-Stammdaten-data.zip', 'r') as zipObj:
            zipObj.extractall()

    search = base_url + '/ajax/filterlist/de/services/opendata/00000-543410?offset='
    status_code = 200
    offset = 0
    with tqdm() as pbar:
        while status_code == 200:
            response = requests.get(search + f'{offset}')
            offset += 5
            status_code = response.status_code
            soup = BeautifulSoup(response.content, 'html.parser')
            if len(soup.find_all('a')) < 1:
                break
            for elem in soup.find_all('a'):
                get_xml(base_url + elem.attrs['href'])
                pbar.update()

