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

def calculate_age(born):
        if born is None: 
                return None
        today = date.today()
        return int(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))

si = BtPlenar(cnx)

query = """SELECT mandat.art, mdb.geschlecht, COUNT(*), fraktion.name_kurz, mdb.kinder, mdb.geburtsdatum
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

i = 0

data_arr = [] 

raw_data = si.query(query, ['Mandat', 'Geschlecht', 'Applaus / Rede', 'Fraktion', 'Kinder int', 'Geburtsdatum date'])


df = pd.DataFrame([raw_data[key] for key in raw_data])
df['Kinder int'] = df['Kinder int'].fillna(0)
df.dropna(inplace=True)
df.loc[df['Kinder int'] == 0 , 'Kinder'] = 'keine'
df.loc[(df['Kinder int'] > 0) & (df['Kinder int'] < 3), 'Kinder'] = '0 bis 2'
df.loc[df['Kinder int'] > 2, 'Kinder'] = 'mehr als 2'

geburtsdatum = df['Geburtsdatum date']
df['Applaus / Rede'] = df['Applaus / Rede'].apply(lambda x: x-1)
year = timedelta(days=365)

df = df[geburtsdatum.notnull()]

df.loc[geburtsdatum > (date.today() - 30 * year), 'Alter'] = 'unter 30'
df.loc[(geburtsdatum <= (date.today() - 30 * year)) & (geburtsdatum > (date.today() - 40 * year)), 'Alter'] = '30 bis 40'
df.loc[(geburtsdatum <= (date.today() - 40 * year)) & (geburtsdatum > (date.today() - 50 * year)), 'Alter'] = '40 bis 50'
df.loc[(geburtsdatum <= (date.today() - 50 * year)) & (geburtsdatum > (date.today() - 60 * year)), 'Alter'] = '50 bis 60'
df.loc[(geburtsdatum <= (date.today() - 60 * year)) & (geburtsdatum > (date.today() - 70 * year)), 'Alter'] = '60 bis 70'
df.loc[(geburtsdatum <= (date.today() - 70 * year)) , 'Alter'] = '70 und mehr'

df['Alter / Jahre'] = geburtsdatum.apply(lambda row: calculate_age(row))


#sns.violinplot(x="Mandat", y="Applaus / Rede", data=df, split=True, hue="Geschlecht", gridsize=50, inner="quartile", palette="Set3", cut=0, width=1)
#plt.rc('axes', axisbelow=True)
#plt.grid()
#g = sns.factorplot(x="Alter", y="Applaus / Rede", col="Fraktion", data=df, saturation=.2, kind="violin", ci=None, aspect=2, palette=sns.color_palette( ['#00FFFF','#FFFF00'], n_colors=2), order=['unter 30','30 bis 40', '40 bis 50', '50 bis 60', '60 bis 70', '70 und mehr'])

#g = sns.factorplot(x="Alter", y="Applaus / Rede", col="Fraktion", hue="Geschlecht", data=df, size=5 ,kind="swarm", ci=None, aspect=2, order=['unter 30','30 bis 40', '40 bis 50', '50 bis 60', '60 bis 70', '70 und mehr'])


g = sns.PairGrid(df, vars=['Alter / Jahre','Applaus / Rede'])


g = g.map_upper(sns.violinplot)
g = g.map_diag(sns.kdeplot, lw=3, legend=False)
g = g.map_lower(sns.kdeplot)

plt.figure()
#g = g.map_lower(sns.jointplot, kind="kde")

#g = (sns.jointplot('Alter / Jahre', 'Applaus / Rede', data=df)
 #       )
#sns.distplot(df['Alter / Jahre'])
sns.regplot(data=df, x='Alter / Jahre', y='Applaus / Rede')
plt.figure()
o = ['unter 30', '30 bis 40', '40 bis 50', '50 bis 60', '60 bis 70', '70 und mehr']
sns.boxplot(data=df, x='Alter', y='Applaus / Rede', hue='Geschlecht', order=o)

plt.figure()
sns.regplot(data=df, x='Kinder int', y='Applaus / Rede')



#plt.figure()
print(df[['Alter / Jahre','Applaus / Rede']].values)
#sns.lmplot(data=df, x='Alter / Jahre', y='Applaus / Rede')
#g = sns.FacetGrid(df, col="Fraktion",  row="Geschlecht", size=3)
#g.map(scatter, "Applaus / Rede", "Alter")


#(g.set_titles("{col_name}")
#    .despine(left=True))



#for ax1 in g.axes:
#        for idx in range(len(ax1)):
#                ax1[idx].grid()
#                plt.setp(ax1[idx].collections, alpha=.5)

plt.show()