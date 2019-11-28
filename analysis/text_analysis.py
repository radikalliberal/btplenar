import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib as mpl
import matplotlib.colors as cols
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
import pandas as pd
from scipy import stats
from math import log
import seaborn as sns
import pymysql.cursors
from BtPlenar import BtPlenar
from datetime import date,timedelta
import scipy.stats as stats
from sklearn.naive_bayes import BernoulliNB

cnx = pymysql.connect(user='root',
                      password='',
                      host='127.0.0.1',
                      charset='utf8mb4',
                      database='btplenar')

si = BtPlenar(cnx)

query = """SELECT absatz.`Text`, fraktion.name_kurz
        FROM absatz
        LEFT JOIN (rede, mdb, mandat, fraktion) 
        ON (rede.idrede = absatz.rede 
        AND mdb.idMdB = rede.redner
        AND mandat.mdb = mdb.idMdB
        AND fraktion.idFraktion = mandat.fraktion)
        WHERE Rede.kurzintervention is null
        AND mandat.wahlp = 19;"""

raw_data = si.query(query)

df = pd.DataFrame([raw_data[key] for key in raw_data])