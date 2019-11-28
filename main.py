from analysis.BtPlenar import BtPlenar
import xml.etree.ElementTree as ET
from glob import glob
from util import *

if __name__ == "__main__":

    get_data()

    conn_settings = {'user': 'root',
                     'password': '',
                     'host': '127.0.0.1',
                     'charset': 'utf8mb4',
                     'database': 'btplenar'}

    with BtPlenar(conn_settings) as btp:
        root = ET.parse('./data/MDB_STAMMDATEN.XML').getroot()
        btp.readStammdaten(root)
        sitzungen = glob('./data/*-data.xml')
        with tqdm(total=len(sitzungen), desc='parsing Sitzungen') as pbar:
            for sitzung in sitzungen:
                with open(sitzung, 'r', encoding='utf-8') as f:
                    xml_data = f.read()
                root = ET.fromstring(xml_data)
                btp.evalSitzung(root, pbar)
                pbar.update()
