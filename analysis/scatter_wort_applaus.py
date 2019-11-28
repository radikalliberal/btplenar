
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from BtPlenar import BtPlenar
conn_settings = {'user': 'root',
                 'password': '',
                 'host': '127.0.0.1',
                 'charset': 'utf8mb4',
                 'database': 'btplenar'}

with BtPlenar(conn_settings) as btp:

    query = """SELECT MdB.Vorname, MdB.Nachname, mdb.geschlecht, tagesordnungspunkt.thema, Fraktion.name_kurz, COUNT(*) as Beifall,
    (SELECT COUNT(*) 
    FROM absatz 
    LEFT JOIN rede as r
    ON (r.idRede = Absatz.rede)
    Where r.idRede = rede.idRede) AS Absätze,
    SUM(LENGTH(absatz.text) - LENGTH(REPLACE(absatz.text, ' ', '')) + 1) as woerter,  
    SUM(LENGTH(absatz.text)) as stringlength, 
    SUM(LENGTH(absatz.text)) / SUM(LENGTH(absatz.text) - LENGTH(REPLACE(absatz.text, ' ', '')) + 1) as avg_word_length
    FROM Beifall
    LEFT JOIN (Rede, MdB, Absatz, Mandat, Tagesordnungspunkt, sitzung, Fraktion) 
    ON (Rede.idRede = Absatz.Rede 
    AND beifall.Absatz = Absatz.idAbsatz
    AND Tagesordnungspunkt.idTagesordnungspunkt = Rede.top
    AND sitzung.idSitzung = Tagesordnungspunkt.sitzung
    AND Rede.redner = MdB.idMdB
    AND Mandat.wahlp = sitzung.wahlperiode
    AND Mandat.MdB = MdB.idMdB
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
    AND Fraktion.name_kurz = "FDP"
    group by Rede.idRede, Fraktion.idFraktion;"""
    """having count(*) > 2;"""

    raw_data = btp.query(query)

df = pd.DataFrame(raw_data)
df.dropna(inplace=True)
df['Beifall'] = df['Beifall'].apply(lambda x: x - 1)
#sns.set(style="ticks")
new_df = df[['geschlecht', 'Beifall', 'woerter']]
new_df[['Beifall', 'woerter']] = new_df[['Beifall', 'woerter']].astype(int)
sns.pairplot(new_df, hue="geschlecht")
sns.jointplot('woerter', 'Beifall', data=new_df, kind="kde", color="#4CB391")
#sns.violinplot(x="woerter", y="Applaus / Rede", data=df, split=True, hue="geschlecht", gridsize=50, inner="quartile", palette="Set3", cut=0, width=1)
plt.show()