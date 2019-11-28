import requests
import pymysql.cursors
from BtPlenar import BtPlenar
import xml.etree.ElementTree as ET
from glob import glob
from tqdm import tqdm

if __name__ == "__main__":
    cnx = pymysql.connect(user='root',
                          password='',
                          host='127.0.0.1',
                          charset='utf8mb4',
                          database='btplenar')

    si = BtPlenar(cnx)

    
    root = ET.parse('./data/MDB_STAMMDATEN.XML').getroot()
    si.readStammdaten(root)

    sitzungen = glob('./data/*-data.xml')
    with tqdm(total=len(sitzungen), desc='parsing Sitzungen') as pbar:
        for sitzung in sitzungen:
            with open(sitzung, 'r', encoding='utf-8') as f:
                xml_data = f.read()
            root = ET.fromstring(xml_data)
            si.evalSitzung(root, pbar)
            pbar.update()


    si.cursor.close()
    si.cnx.close()
    
