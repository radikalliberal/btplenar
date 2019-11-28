import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymysql.cursors
import scipy.stats as stats
import math

from BtPlenar import BtPlenar

cnx = pymysql.connect(user='root',
                      password='secret',
                      host='127.0.0.1',
                      charset='utf8mb4',
                      database='btplenar')

si = BtPlenar(cnx)

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
group by Rede.idRede, Fraktion.idFraktion;"""
"""having count(*) > 2;"""

i = 0

data_arr = []

raw_data = si.query(query)
df = pd.DataFrame([raw_data[key] for key in raw_data])
cols = df.columns
df.dropna(inplace=True)
df['Beifall'] = df['Beifall'].apply(lambda x: x - 1)

df['Applaus / Absatz'] = df.apply(lambda row: (row['Beifall'] / row['Absätze']), axis=1)
df['Applaus / Wort'] = df.apply(lambda row: (row['Beifall'] / row['woerter']), axis=1)

# dens_u = sm.nonparametric.KDEMultivariate(data=[df['Beifall'].values ,df['Absätze'].values], var_type='cc', bw='normal_reference')
# data = [df['Beifall'].values ,df['Absätze'].values]
# print(data)
# kdemv = sm.nonparametric.KDEMultivariate(data, var_type='uu')
# pdf = kdemv.pdf()

# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import axes3d
# from matplotlib import cm
# import numpy

# fig = plt.figure()

# plt.plot(pdf)

print(df['name_kurz'].unique())
linke = df.where(df['name_kurz'] == 'LINKE')
linke.dropna(inplace=True)

size = int(math.sqrt(len(df['name_kurz'].unique())) + 1)

max_y = 0

fitting = True
max_value = 16
mean_claps = {}

for k, fraktion in enumerate(df['name_kurz'].unique()):
    if fraktion == 'fraktionslos':
        continue
    legend_entries = []
    stat = {}
    for geschlecht, color in zip(['weiblich', 'männlich'], ['r', 'b']):
        plt.figure(k + 1)
        frame = df.where((df['geschlecht'] == geschlecht) & (df['name_kurz'] == fraktion)).dropna()
        data = frame['Applaus / Wort'].values.astype(float) * 100
        entries, bin_edges, patches = plt.hist(data, bins=int(max_value)*2, range=[-0.25, max_value - 0.25], normed=fitting, alpha=0.5, color=color)
        if max_y < max(entries): max_y = max(entries)
        shape, loc, scale = stats.lognorm.fit(entries, floc=0)

        # sigma = np.std(np.log(data))
        sigma = np.log(np.percentile(data, 95) / np.mean(data)) / 1.645
        # mu = np.mean(np.log(data))
        mu = np.log(np.mean(data)) - (sigma ** 2 / 2)
        x = np.linspace(min(bin_edges), max(bin_edges), 10000)


        if fitting:
            shape, loc, scale = stats.lognorm.fit(data)
            x_2 = np.arange(0, int(max_value)*2)
            rv = stats.lognorm(shape, loc=loc, scale=scale)
            mean = rv.mean()
            std = rv.std()
            kstest = stats.kstest(data, rv.cdf)
            chi = stats.chisquare(entries * frame['name_kurz'].count(), rv.pdf(x_2) * frame['name_kurz'].count())
            stat[geschlecht] = mean

            plt.plot(x, rv.pdf(x), color=color, linestyle=':', linewidth=2, alpha=0.75)
            legend_entries.append(
                mlines.Line2D([], [], linestyle=':', color=color, label=r'Lognormal: $\mu =$ ' + f'{mean:.2f}' +
                                                                 r' $\sigma = $' + f'{std:.2f}' +
                                                                 r' $\chi^2 = $' + f'{chi.statistic:.2f}' +
                                                                 f' p-value = {chi.pvalue:.2e}'
                                                                 f' n = {frame["name_kurz"].count()}'))

            '''
            mu, std = stats.norm.fit(data)
            rv = stats.norm(mu, std)
            kstest = stats.kstest(data, rv.cdf, alternative='two-sided')
            chi = stats.chisquare(entries * frame['name_kurz'].count(), rv.pdf(x_2) * frame['name_kurz'].count())
            mean = rv.mean()
            std = rv.std()

            plt.plot(x, rv.pdf(x), color=color, linestyle='-.', linewidth=2, alpha=0.75)
            legend_entries.append(
                mlines.Line2D([], [], linestyle='-.', color=color, label=r'Normal: $\mu =$ ' + f'{mean:.2f}' +
                                                                         r' $\sigma = $' + f'{std:.2f}' +
                                                                         r' $\chi^2 = $' + f'{chi.statistic:.2f}' +
                                                                         f' p-value = {chi.pvalue:.2e}'
                                                                         f' n = {frame["name_kurz"].count()}'))

            a, b, loc, scale = stats.beta.fit(data)
            rv = stats.beta(a, b, loc=loc, scale=scale)
            kstest = stats.kstest(data, rv.cdf)
            chi = stats.chisquare(entries * frame['name_kurz'].count(), rv.pdf(x_2) * frame['name_kurz'].count())
            mean = rv.mean()
            std = rv.std()

            plt.plot(x, rv.pdf(x), color=color, linestyle='-', linewidth=2, alpha=0.75)
            legend_entries.append(
                mlines.Line2D([], [], linestyle='-', color=color, label=r'beta: $\mu =$ ' + f'{mean:.2f}' +
                                                                        r' $\sigma = $' + f'{std:.2f}' +
                                                                        r' $\chi^2 = $' + f'{chi.statistic:.2f}' +
                                                                        f' p-value = {chi.pvalue:.2e}'
                                                                        f' n = {frame["name_kurz"].count()}'))

            loc, scale = stats.gumbel_r.fit(data)
            rv = stats.gumbel_r(loc, scale)
            kstest = stats.kstest(data, rv.cdf)
            chi = stats.chisquare(entries * frame['name_kurz'].count(), rv.pdf(x_2) * frame['name_kurz'].count())
            mean = rv.mean()
            std = rv.std()

            plt.plot(x, rv.pdf(x), color=color, linestyle='-', linewidth=2, alpha=0.75)
            legend_entries.append(
                mlines.Line2D([], [], linestyle='-', color=color, label=r'gumbel_r: $\mu =$ ' + f'{mean:.2f}' +
                                                                        r' $\sigma = $' + f'{std:.2f}' +
                                                                        r' $\chi^2 = $' + f'{chi.statistic:.2f}' +
                                                                        f' p-value = {chi.pvalue:.2e}'
                                                                        f' n = {frame["name_kurz"].count()}'))'''



        # calculate binmiddles
        # bin_middles = 0.5*(bin_edges[1:] + bin_edges[:-1])

        # poisson function, parameter lamb is the fit parameter
        # def poisson(k, lamb):
        #        return (lamb**k/factorial(k)) * np.exp(-lamb)

        # fit with curve_fit
        # parameters, cov_matrix = curve_fit(poisson, bin_middles, entries)

        # plot poisson-deviation with fitted parameter
        # x_plot = np.linspace(0, 20, 1000)

        # plt.plot(x_plot, poisson(x_plot, *parameters), 'r-', lw=2)
    plt.title(f'{fraktion}')
    plt.legend(handles=legend_entries)
    mean_claps[fraktion] = stat

for num in range(1, 7):
    plt.figure(num)
    plt.ylim([0, max_y * 1.05])

plt.show()
print(mean_claps)

