import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib as mpl
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
import pandas as pd
from scipy import stats
from math import log
import seaborn as sns; sns.set()
import pymysql.cursors
from BtPlenar import BtPlenar
from datetime import date,timedelta

cnx = pymysql.connect(  user='root', 
                        password='00qrcCIIan',
                        host='127.0.0.1',
                        charset='utf8mb4',
                        database='btplenar')

si = BtPlenar(cnx)

query = """SELECT rede.idrede, mandat.art, mdb.geschlecht, COUNT(*), fraktion.name_kurz, mdb.kinder, mdb.geburtsdatum
        FROM beifall
        LEFT JOIN (rede, mdb, absatz, mandat, tagesordnungspunkt, sitzung, fraktion) 
        ON (rede.idrede = absatz.rede 
        AND beifall.absatz = absatz.idAbsatz
        AND tagesordnungspunkt.idTagesordnungspunkt = rede.top
        AND sitzung.idSitzung = tagesordnungspunkt.sitzung
        AND rede.redner = mdb.idMdB
        AND mandat.wahlp = sitzung.wahlperiode
        AND mandat.mdb = mdb.idMdB
        AND beifall.von = fraktion.idFraktion)
        WHERE rede.kurzintervention is null
        AND rede.antwort_kurzintervention is null
        AND tagesordnungspunkt.befragung = 0
        group by rede.idrede, fraktion.idfraktion;"""

query2 ="""SELECT rede.idrede, COUNT(absatz.idabsatz), mdb.Nachname, tagesordnungspunkt.thema
        FROM absatz
        LEFT JOIN (rede, mdb, mandat, tagesordnungspunkt, sitzung, fraktion)
        ON (rede.idrede = absatz.rede 
        AND tagesordnungspunkt.idTagesordnungspunkt = rede.top
        AND sitzung.idSitzung = tagesordnungspunkt.sitzung
        AND rede.redner = mdb.idMdB
        AND mandat.wahlp = sitzung.wahlperiode
        AND mandat.mdb = mdb.idMdB
        AND fraktion.idFraktion = mandat.fraktion)
        WHERE rede.kurzintervention is null
        AND rede.antwort_kurzintervention is null
        AND tagesordnungspunkt.befragung = 0
        group by rede.idrede, fraktion.idfraktion;"""

i = 0

data_arr = [] 

raw_data = si.query(query)
raw_data = si.query(query, ['Redeid', 'Mandat', 'Geschlecht', 'Applaus / Rede', 'Fraktion', 'Kinder int', 'Geburtsdatum date'])
df = pd.DataFrame([raw_data[key] for key in raw_data])
print(df)
raw_data = si.query(query2, ['Redeid', 'Absätze', 'Nachname', 'Thema'])
df2 = pd.DataFrame([raw_data[key] for key in raw_data])

print(df2)
df = df.merge(df2, left_on='Redeid', right_on='Redeid', how='outer')

df['Kinder int'] = df['Kinder int'].fillna(0)
df.dropna(inplace=True)
df['Applaus / Rede'] = df['Applaus / Rede'].apply(lambda x: x-1)
df.loc[df['Kinder int'] == 0, 'Kinder'] = 'keine'
df.loc[(df['Kinder int'] > 0) & (df['Kinder int'] < 3), 'Kinder'] = '0 bis 2'
df.loc[df['Kinder int'] > 2, 'Kinder'] = 'mehr als 2'

df['Applaus / Absatz'] = df.apply(lambda row: (row['Applaus / Rede'] / row['Absätze']), axis=1)

print(df)

frauen = df.where(df['Geschlecht'] == 'weiblich').dropna()
männer = df.where(df['Geschlecht'] == 'männlich').dropna()

print()

gs = GridSpec(4, 2)
ax =[plt.subplot(gs[0, 0]), 
    plt.subplot(gs[0, 1]), 
    plt.subplot(gs[1, 0]),
    plt.subplot(gs[1, 1]),
    plt.subplot(gs[2, 0]),
    plt.subplot(gs[2, 1]),
    plt.subplot(gs[3, :])]

plt.figure()

gs2 = GridSpec(4, 2)
ax2 =[plt.subplot(gs2[0, 0]), 
    plt.subplot(gs2[0, 1]), 
    plt.subplot(gs2[1, 0]),
    plt.subplot(gs2[1, 1]),
    plt.subplot(gs2[2, 0]),
    plt.subplot(gs2[2, 1]),
    plt.subplot(gs[3, :])]

print(df['Fraktion'].unique())

for idx, frak in enumerate(df['Fraktion'].unique()):
    f = frauen.where((frauen['Fraktion'] == frak) & (frauen['Applaus / Absatz'] > 0)).dropna()
    m = männer.where((männer['Fraktion'] == frak) & (männer['Applaus / Absatz'] > 0)).dropna()
    sns.distplot(f['Applaus / Absatz'], ax=ax[idx], bins=40)
    sns.distplot(m['Applaus / Absatz'], ax=ax[idx], bins=40)
    ax[idx].set_title(frak)


for idx, frak in enumerate(df['Fraktion'].unique()):
    f = frauen.where((frauen['Fraktion'] == frak) & (frauen['Applaus / Absatz'] > 0)).dropna()
    m = männer.where((männer['Fraktion'] == frak) & (männer['Applaus / Absatz'] > 0)).dropna()
    sns.regplot(x='Absätze', y='Applaus / Rede',data=f, ax=ax2[idx], scatter_kws={'alpha': 0.3}, line_kws={'alpha': 0.3, 'color': 'r'}, color=sns.xkcd_rgb["pale red"], marker="o", robust=True)
    sns.regplot(x='Absätze', y='Applaus / Rede',data=m, ax=ax2[idx], scatter_kws={'alpha': 0.3}, line_kws={'alpha': 0.3, 'color': 'b'}, color=sns.xkcd_rgb["denim blue"], marker="+", robust=True)
    #sns.distplot(m['Applaus / Absatz'], ax=ax2[idx], bins=40)
    ax2[idx].set_title(frak)

#df.hist(bins=20)
plt.show()