import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib as mpl
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
import pandas as pd
import pymysql.cursors
from BtPlenar import BtPlenar

def plotit(dataframe, si, title, filename, y_maximum):
    parteien = [si.getEntryById('fraktion', i)[0]['name'] for i in range(6) ]
    parteien_weniger = [si.getEntryById('fraktion', i)[0]['name']+'_weniger' for i in range(6) ]
    parteien_short = ['SPD', 'CDU/CSU', 'LINKE', 'FDP', 'GRÜNE', 'AfD']
    imgs = ['./small/spd.png', './small/cducsu.png', './small/linke.png', './small/fdp.png', './small/grüne.png', './small/afd.png']


    alle = dataframe[parteien].values
    paar = dataframe[parteien_weniger].values

    #fig = mpl.figure.Figure()

    #for x in range(int(alle.shape[1]/9)+1):
    x = 0    

    left  = 0.1  # the left side of the subplots of the figure
    right = 0.98    # the right side of the subplots of the figure
    bottom = 0.1   # the bottom of the subplots of the figure
    top = 0.82      # the top of the subplots of the figure
    wspace = 0.1   # the amount of width reserved for blank space between subplots,
                # expressed as a fraction of the average axis width
    hspace = 0.6   # the amount of height reserved for white space between subplots,
                # expressed as a fraction of the average axis height
    #plt.subplots_adjust(left=left, top=top, hspace=hspace, bottom=bottom, right=right)


    fig, ax = plt.subplots(figsize=(8, 5), dpi=160, facecolor='w', edgecolor='k')
    plt.subplots_adjust(bottom=0.2)
    print(np.sum(alle) + np.sum(paar))
    data = np.ndarray([])
    #fig = plt.figure()
    #data = [ alle[i][k], paar[i][k] for k in range(len(paar[i]))]
    #ax[i].pie(data.astype(float), colors=('#ff0000', '#800000', '#0000ff', '#000080', '#cc3300', '#802000', '#ffe680', '#ffcc00', '#339966', '#206040', '#33ccff', '#00ace6' ) , autopct='%1.1f%%', shadow=True)
    plt.bar(np.arange(len(parteien)), alle )
    #ax[i].set_xticklabels(['']+ parteien_short)
    plt.bar(np.arange(len(parteien)), paar, bottom=alle.astype(int))
    plt.legend(['Alle', 'nicht alle'])
    #plt.set_title(f'{df["vorname"][i]}, {df["nachname"][i]} : {df["fraktion"][i]}\n{"{:%d.%m.%Y}".format(df["datum"][i])}')
    plt.title(title)
    plt.ylim([0, y_maximum])
    plt.grid(axis='y', alpha=0.2)
    plt.xlabel('\n\nFraktion')
    plt.ylabel('Häufigkeit Klatschen')
    #x[i].set_subtitle(df["thema"][i], fontsize=7)
    plt.xticks(rotation=35)

    for j in range(6):
        im = plt.imread(imgs[j])
        imagebox = OffsetImage(im, zoom=0.125)
        imagebox.image.axes = ax

        ab = AnnotationBbox(imagebox, (j, 0),
                            xybox=(0, -20),
                            xycoords='data',
                            boxcoords="offset points",
                            pad=0)

        ax.add_artist(ab)
    fig.savefig(filename + '.png')
    #plt.show()

cnx = pymysql.connect(  user='root', 
                        password='00qrcCIIan',
                        host='127.0.0.1',
                        charset='utf8mb4',
                        database='btplenar')

si = BtPlenar(cnx)
    
#si.everybodyClap()
#si.count()
#print(si.getRede(191708900))
#print(si.getMaxId('beifall'))
#results = si.everybodyClap()
#for key in results.keys():
#    print(results[key])
#beifall = si.count()
#print(beifall)

beifall = si.get_most_clapped_speech()
beifall_all = si.claps_pro_fraktion()
beifall_antrag_afd = si.antraegeDerAfd()
beifall_kein_antrag_afd = si.antraegeDerAfd('NOT')

#del beifall[0]

#print(beifall)


df = pd.DataFrame([beifall[key] for key in beifall])
#print(df.count())
 
df['partei'] = np.array([key for key in beifall])
#df = df.set_index('partei')
#print(df)
#print([key for key in beifall])
#ax = plt.imshow(df, cmap='Wistia', interpolation='nearest')
#plt.show()


for index, d in df.iterrows():
    frak = str(d["fraktion"]).replace('/','')
    plotit(d, si, f'{d["vorname"]}, {d["nachname"]} {d["fraktion"]} {"{:%d-%m-%Y}".format(d["datum"])}',  
            f'{d["nachname"]}{frak}{"{:%d-%m-%Y}".format(d["datum"])}', 22)
    print(f'{d["vorname"]}, {d["nachname"]} {d["fraktion"]} {"{:%d-%m-%Y}".format(d["datum"])}\n{d["thema"]}\n\n\n')

df = pd.DataFrame([beifall_all[key] for key in beifall_all])

for index, d in df.iterrows():
    frak = str(d["fraktion"]).replace('/', '')
    plotit(d, si, f'Beifall für {d["fraktion"]}', f'Beifall nach Fraktion {frak}', 1200)

df = pd.DataFrame([beifall_antrag_afd[key] for key in beifall_antrag_afd])
print(df)
for index, d in df.iterrows():
    frak = str(d["fraktion"]).replace('/', '')
    plotit(d, si, f'Beifall für {d["fraktion"]}', f'Beifall Antrag AfD nach Fraktion {frak}', 400)

df = pd.DataFrame([beifall_kein_antrag_afd[key] for key in beifall_kein_antrag_afd])
for index, d in df.iterrows():
    frak = str(d["fraktion"]).replace('/', '')
    plotit(d, si, f'Beifall für {d["fraktion"]}', f'Beifall nicht Antrag AfD nach Fraktion {frak}', 1000)

si.cursor.close()
si.cnx.close()

def old_plot():
    parteien = [si.getEntryById('fraktion', i)[0]['name'] for i in range(6) ]
    parteien_weniger = [si.getEntryById('fraktion', i)[0]['name']+'_weniger' for i in range(6) ]
    parteien_short = ['SPD', 'CDU/CSU', 'LINKE', 'FDP', 'GRÜNE', 'AfD']
    imgs = ['./small/spd.png', './small/cducsu.png', './small/linke.png', './small/fdp.png', './small/grüne.png', './small/afd.png']

    si.cursor.close()
    si.cnx.close()

    print(df[parteien])

    alle = df[parteien].values
    paar = df[parteien_weniger].values

    #fig = mpl.figure.Figure()

    #for x in range(int(alle.shape[1]/9)+1):
    x = 0    
    gs = GridSpec(3, 3)
    ax =[plt.subplot(gs[0, 0]), 
        plt.subplot(gs[0, 1]), 
        plt.subplot(gs[0, 2]),
        plt.subplot(gs[1, 0]),
        plt.subplot(gs[1, 1]),
        plt.subplot(gs[1, 2]),
        plt.subplot(gs[2, 0]),
        plt.subplot(gs[2, 1]),
        plt.subplot(gs[2, 2])]

    left  = 0.1  # the left side of the subplots of the figure
    right = 0.98    # the right side of the subplots of the figure
    bottom = 0.1   # the bottom of the subplots of the figure
    top = 0.95      # the top of the subplots of the figure
    wspace = 0.1   # the amount of width reserved for blank space between subplots,
                # expressed as a fraction of the average axis width
    hspace = 0.6   # the amount of height reserved for white space between subplots,
                # expressed as a fraction of the average axis height
    plt.subplots_adjust(left=left, top=top, hspace=hspace, bottom=bottom, right=right)

    maximum = np.max(alle + paar) 

    #print(alle)
    #fig, ax = plt.subplots()
    for i in range(7):
        
        data = np.ndarray([])
        #data = [ alle[i][k], paar[i][k] for k in range(len(paar[i]))]
        #ax[i].pie(data.astype(float), colors=('#ff0000', '#800000', '#0000ff', '#000080', '#cc3300', '#802000', '#ffe680', '#ffcc00', '#339966', '#206040', '#33ccff', '#00ace6' ) , autopct='%1.1f%%', shadow=True)
        ax[i].bar(np.arange(len(parteien)), alle[i] )
        #ax[i].set_xticklabels(['']+ parteien_short)
        ax[i].bar(np.arange(len(parteien)), paar[i], bottom=alle[i].astype(int))
        ax[i].legend(['Alle', 'nicht alle'])
        #ax[i].set_title(f'{df["vorname"][i]}, {df["nachname"][i]} : {df["fraktion"][i]}\n{"{:%d.%m.%Y}".format(df["datum"][i])}')
        ax[i].set_title(f' {df["fraktion"][i]}')
        ax[i].set_ylim([0, int(maximum)])
        ax[i].grid(axis='y', alpha=0.2)
        #x[i].set_subtitle(df["thema"][i], fontsize=7)
        
        plt.xticks(rotation=35)

        for j in range(6):
            im = plt.imread(imgs[j])
            imagebox = OffsetImage(im, zoom=0.15)
            imagebox.image.axes = ax[i]

            ab = AnnotationBbox(imagebox, (j, 0),
                                xybox=(0, -20),
                                xycoords='data',
                                boxcoords="offset points",
                                pad=0)

            ax[i].add_artist(ab)
    plt.show()


"""SELECT SUM(mdb.geschlecht = 'männlich'), SUM(mdb.geschlecht = 'weiblich')
FROM beifall
LEFT JOIN (rede, mdb, absatz, mandat) 
ON (rede.idrede = absatz.rede 
AND beifall.absatz = absatz.idAbsatz
AND rede.redner = mdb.idMdB
AND mandat.mdb = mdb.idMdB ) ;"""

"""SELECT SUM(mdb.geschlecht = 'männlich'), SUM(mdb.geschlecht = 'weiblich')
FROM rede
LEFT JOIN mdb
ON mdb.idmdb = rede.redner;"""

"""SELECT wahlperiode.idWahlperiode ,SUM(mdb.geschlecht = 'männlich'), SUM(mdb.geschlecht = 'weiblich')
from mandat
LEFT JOIN (mdb, wahlperiode)
ON mdb.idmdb = mandat.mdb
AND wahlperiode.idWahlperiode = mandat.wahlp
GROUP BY wahlperiode.idWahlperiode;"""