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
        AND mandat.fraktion = Fraktion.idFraktion)
        WHERE Rede.kurzintervention is null
        AND Rede.antwort_kurzintervention is null
        AND Tagesordnungspunkt.befragung = 0
        AND (SELECT COUNT(*) 
            FROM absatz 
            LEFT JOIN rede as r
            ON (r.idRede = Absatz.rede)
            Where r.idRede = rede.idRede) > 10
        AND beifall.von = fraktion.idFraktion
        AND mandat.bis is NULL
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


#sns.distplot(df['Absätze'].values, bins=[x for x in range(0,56,2)],color='b')
plt.figure()

sns.violinplot(x="Mandat", y="Applaus / Rede", data=df, split=True, hue="Geschlecht", gridsize=50, inner="quartile", palette="Set3", cut=0, width=1)


#sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df, split=True, col="Geschlecht", gridsize=50, palette="Set3", cut=0, width=1)
#sns.boxplot(x="Fraktion", y="Applaus / Rede", hue="Geschlecht", data=df, palette="Set1")
#sns.stripplot(x="Fraktion", y="Applaus / Rede", hue="Mandat", data=df, palette="Set1", jitter=0.3, size=3 )
#ax[4].grid()
#ax[4].violinplot(data_arr, points=40, showmeans=True, showextrema=True, showmedians=True)


#raw_data = si.query(query, ['Mandat', 'Geschlecht', 'Applaus / Rede', 'Fraktion'])
#df = pd.DataFrame([raw_data[key] for key in raw_data])
plt.rc('axes', axisbelow=True)

g = sns.factorplot(x="Geschlecht", y="Applaus / Rede", col="Fraktion", data=df, saturation=.2, kind="violin", ci=None, aspect=.6, palette=sns.color_palette( ['#0000FF','#FF0000'], n_colors=2))
for ax1 in g.axes:
        for idx in range(len(ax1)):
                ax1[idx].grid()
                plt.setp(ax1[idx].collections, alpha=.4)


fraks = df['Fraktion'].unique()


frauen = df.where(df['Geschlecht'] == 'weiblich').dropna()
männer = df.where(df['Geschlecht'] == 'männlich').dropna()

def alpha_cmap(cmap):
    my_cmap = cmap(np.arange(cmap.N))
    # Set a square root alpha.
    x = np.linspace(0.4, 0.5, cmap.N)
    my_cmap[:,-1] = x 
    my_cmap = cols.ListedColormap(my_cmap)

    return my_cmap

for frak in fraks.T:
        plt.figure()
        if frak is None: continue
        #g = sns.factorplot(x="Geschlecht", y="Applaus / Rede", col="Mandat", data=df.where(df['Fraktion'] == frak) , saturation=.2, kind="box", ci=None, aspect=.6, palette=sns.color_palette( ['#0000FF','#FF0000'], n_colors=2))
        f = frauen.where(frauen['Fraktion'] == frak).dropna()
        m = männer.where(männer['Fraktion'] == frak).dropna()
        d = df.where(df['Fraktion'] == frak).dropna()
        #sns.distplot(m['Applaus / Rede'].values, bins=[x for x in range(0,26,1)], color='b')
        #sns.distplot(f['Applaus / Rede'].values, bins=[x for x in range(0,26,1)], color='r')
        #sns.lmplot(x='Absätze', y='Applaus / Rede', hue='Geschlecht', truncate=True, size=4, data=d)
        sns.kdeplot(f['Absätze'], f['Applaus / Rede'], n_levels=5,cmap=alpha_cmap(plt.cm.get_cmap('Reds')), cbar=True, shade=True, shade_lowest=False, antialiased=True, bw=1)
        sns.kdeplot(m['Absätze'], m['Applaus / Rede'], n_levels=5, cmap=alpha_cmap(plt.cm.get_cmap('Blues')), cbar=True, shade=True, shade_lowest=False, antialiased=True, bw=1)
        plt.title(frak)
        #for ax1 in g.axes:
        #        for idx in range(len(ax1)):
        #                ax1[idx].grid()
        #                ax1[idx].set_title(frak)
        #                plt.setp(ax1[idx].collections, alpha=.4)


mix = ['#FA5858','#2E2EFE']
weib = ['#FA5858','#FA5858','#FA5858','#FA5858','#FA5858','#FA5858']
mann = ['#2E2EFE','#2E2EFE','#2E2EFE','#2E2EFE','#2E2EFE','#2E2EFE']

plt.figure()


#with sns.color_palette(weib, n_colors=1) as palette:
#    ax[0] = sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df.where(df['Geschlecht'] == 'weiblich'), inner=None, palette=palette, width=1)
#with sns.color_palette(mann, n_colors=1) as palette:
##sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df.where(df['Geschlecht'] == 'männlich'), split=True, gridsize=50, palette="Blues_d", cut=0, width=1)
#    
#    ax[0] += sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df.where(df['Geschlecht'] == 'männlich'), inner=None, palette=palette, width=1)
#
#plt.setp(ax[0].collections, alpha=.4)
#sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df, hue="Geschlecht", gridsize=50, inner="box", palette=sns.color_palette( ['#FA5858','#2E2EFE'], n_colors=2), width=1, saturation=0.5)
#sns.violinplot(x="Fraktion", y="Applaus / Rede", data=df, hue="Geschlecht", gridsize=50, inner="quartile", palette=sns.color_palette( ['#FFFFFF'], n_colors=1), width=1, saturation=0.5)
#plt.setp(ax[1].collections, alpha=.4)
#sns.boxplot(x="Fraktion", y="Applaus / Rede", hue="Geschlecht", data=df, palette="Set1")
#sns.stripplot(x="Fraktion", y="Applaus / Rede", hue="Mandat", data=df, palette="Set1", jitter=0.3, size=3, color='grey')

plt.show()



