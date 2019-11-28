
import matplotlib.pyplot as plt
import pandas as pd
import pymysql.cursors
from IPython.display import display, HTML
import seaborn as sns

from BtPlenar import BtPlenar

cnx = pymysql.connect(user='root',
                      password='00qrcCIIan',
                      host='127.0.0.1',
                      charset='utf8mb4',
                      database='btplenar')

si = BtPlenar(cnx)

query = """select Fraktion.name_kurz, mdb.geschlecht, mandat.art, COUNT(*)
from mandat
LEFT JOIN(mdb, fraktion)
ON (mandat.mdb = mdb.idMdB
AND fraktion.idFraktion = mandat.fraktion)
Where mandat.wahlp = 19
group by fraktion.idFraktion, mdb.geschlecht, mandat.art;"""


raw_data = si.query(query, ['Fraktion', 'Geschlecht', 'Mandat', 'Anzahl'])
df = pd.DataFrame([raw_data[key] for key in raw_data])
df.dropna(inplace=True)
df['Anzahl'] = df['Anzahl'].astype(int)


print(df.groupby(['Fraktion', 'Geschlecht', 'Mandat'])['Anzahl'].aggregate('sum').unstack().fillna(0).to_html())
f = open("yourpage.html", "w")
f.write(df.groupby(['Fraktion', 'Geschlecht', 'Mandat'])['Anzahl'].aggregate('sum').unstack().fillna(0).to_html())
f.close()


#df.pivot_table('Fraktion', 'Geschlecht')
#print(df.head())
#sns.pairplot(df, hue="Geschlecht")
#sns.jointplot('Wörter', 'Applaus / Rede', data=new_df, kind="kde", color="#4CB391")
#sns.violinplot(x="Wörter", y="Applaus / Rede", data=df, split=True, hue="Geschlecht", gridsize=50, inner="quartile", palette="Set3", cut=0, width=1)
#plt.show()