import re
from datetime import datetime
from tqdm import tqdm




class BtPlenar():
    def __init__(self, cnx):
        self.cnx = cnx
        self.cursor = cnx.cursor()

    def query(self, query):
        self.cursor.execute(query)
        idx = 0
        results = {}
        for result in self.cursor:
            d = {}
            for field, val in zip(self.cursor.description, result):
                d[field[0]] = val
            results[idx] = d
            idx += 1
        return results

    def getFields(self, table):
        query = f"""SELECT `COLUMN_NAME` 
                    FROM `INFORMATION_SCHEMA`.`COLUMNS` 
                    WHERE `TABLE_SCHEMA`='btplenar' 
                    AND `TABLE_NAME`='{table}'"""
        self.cursor.execute(query)
        results = []
        for result in self.cursor:
            results += [result[0]]
        return results

    def getRede(self, id):
        if id is None:
            return {0: {'kurzintervention': None}}
        return self.getEntryById('rede', id)

    def getEntryById(self, table, id):
        query = ("SELECT * FROM " + table + " WHERE id" + table + " = " + str(id))
        return self.query(query)


        # fields = ['idrede', 'redner', 'top', 'kurzintervention', 'antwort_kurzintervention']
        # self.cursor.execute(query)
        # for result in self.cursor:
        #    if result is None:
        #        return {}
        #    return dict([(field, val) for field, val in zip(fields, result)])

    def getNewId(self, table):
        query = ("SELECT MAX(id" + table + ") FROM " + table)
        self.cursor.execute(query)
        for result in self.cursor:
            if result[0] is None:
                return 0
            return result[0] + 1

    def getMaxId(self, table, *args):
        query = ("SELECT MAX(id" + table + ") FROM " + table)
        result = self.query(query)
        if result is None:
            return 1
        else:
            return result[0]['MAX(id' + table + ')']

    def getIdByName(self, table, column, word):
        query = ("SELECT id" + table + " FROM " + table + " WHERE " + column + " LIKE '" + word + "'")
        self.cursor.execute(query)
        for result in self.cursor:
            if result[0] is not None:
                return result[0]


    def getNameById(self, table, id):
        query = ("SELECT name FROM " + table + " WHERE id" + table + " = " + str(id))
        self.cursor.execute(query)
        for result in self.cursor:
            if len(result[0]) > 0:
                return result[0]
        return None

    def findId(self, table, id):
        query = ("SELECT id" + table + " = " + str(id) + " FROM " + table)
        self.cursor.execute(query)
        for result in self.cursor:
            if result[0] > 0:
                return True
        return False

    def insertRede(self, id_rede, redner, top_id, ki, aki, ro=None):
        if not self.findId('rede', id_rede):
            self.insert('rede', {'idrede': id_rede,
                                 'redner': redner,
                                 'top': top_id,
                                 'kurzintervention': ki,
                                 'antwort_kurzintervention': aki,
                                 'mitRolle': ro})
            return True

    def insert(self, table, data):
        s = ["%(" + key + ")s" for key in data.keys()]
        try:
            cmd = ("INSERT INTO " + table + "(" + ", ".join(list(data.keys())) + ") VALUES (" + ", ".join(s) + ")")
            self.cursor.execute(cmd, data)
            self.cnx.commit()
        except Exception as e:
            print(f'error for commit\ntable: {table}\ndata: {data}\nmsg: {e}')

    def getAnzahlFraktionen(self):
        query = """SELECT COUNT(*) FROM fraktion"""
        self.cursor.execute(query)
        for result in self.cursor:
            return result[0]

    def findFraktion(self, f):
        frak_id_von = self.getIdByName('fraktion', 'name_kurz', f)
        if frak_id_von is None:
            frak_id_von = self.getIdByName('fraktion', 'name', f)
        if frak_id_von is None:
            return None
        else:
            return frak_id_von

    def insertFraktion(self, name=None, name_kurz=None):

        fraktionen = {'Fraktion der Christlich Demokratischen Union/Christlich - Sozialen Union': 'CDU/CSU',
                      'Fraktion der CDU/CSU (Gast)': 'CDU/CSU',
                      'Fraktion der Sozialdemokratischen Partei Deutschlands': 'SPD',
                      'Fraktion der SPD (Gast)': 'SPD',
                      'Fraktion der Freien Demokratischen Partei': 'FDP',
                      'Fraktion der FDP (Gast)': 'FDP',
                      'Fraktion Die Grünen': 'GRÜNE',
                      'Fraktion Die Grünen/Bündnis 90': 'GRÜNE',
                      'Fraktion Bündnis 90/Die Grünen': 'GRÜNE',
                      'Gruppe Bündnis 90/Die Grünen': 'GRÜNE',
                      'Fraktionslos': 'fraktionslos',
                      'Fraktion DIE LINKE.': 'LINKE',
                      'Gruppe der Partei des Demokratischen Sozialismus': 'LINKE',
                      'Gruppe der Partei des Demokratischen Sozialismus/Linke Liste': 'LINKE',
                      'Fraktion der Partei des Demokratischen Sozialismus': 'LINKE',
                      'Alternative für Deutschland': 'AfD'}

        if name is not None:
            if name in fraktionen:
                res = self.findFraktion(fraktionen[name])
            else:
                res = self.findFraktion(name)
        else:
            res = self.findFraktion(name_kurz)

        if res is None:
            id = self.getNewId('fraktion')
            fraktion_data = {'idfraktion': id,
                             'name': name,
                             'name_kurz': name_kurz if name_kurz is not None else (
                                 fraktionen[name] if name in fraktionen else None)}
            self.insert('fraktion', fraktion_data)
            return id
        else:
            return res

    def findMdb(self, id):
        if id is None or len(id) == 0:
            return None
        query = "SELECT idmdb FROM mdb WHERE bt_id = " + id
        result = self.query(query)
        if not result:
            return None
        else:
            return result[0]['idmdb']

    def insertMdb_from_stamm(self, mdb):
        res = self.findMdb(mdb.find("ID").text)
        if not res:
            id = self.getNewId('mdb')
            string = mdb.find('BIOGRAFISCHE_ANGABEN').find('FAMILIENSTAND').text
            kinder = None
            fam = None
            if string is not None:
                s = re.search(r'(\d+)\sKind', string, re.I | re.S)
                if s is not None:
                    kinder = int(s.group(1))
                s = re.search(r'([^\d,]*),?', string, re.I | re.S)
                if s is not None:
                    fam = s.group(1)

            geb = mdb.find('BIOGRAFISCHE_ANGABEN').find('GEBURTSDATUM').text
            sterb = mdb.find('BIOGRAFISCHE_ANGABEN').find('STERBEDATUM').text

            mdb_data = {'idmdb': id,
                        'bt_id': mdb.find("ID").text,
                        'vorname': mdb.find('NAMEN').find('NAME').find('VORNAME').text,
                        'nachname': mdb.find('NAMEN').find('NAME').find('NACHNAME').text,
                        'geschlecht': mdb.find('BIOGRAFISCHE_ANGABEN').find('GESCHLECHT').text,
                        'titel': mdb.find('NAMEN').find('NAME').find('AKAD_TITEL').text,
                        'geburtsdatum': datetime.strptime(geb, '%d.%m.%Y') if geb is not None else None,
                        'sterbedatum': datetime.strptime(sterb, '%d.%m.%Y') if sterb is not None else None,
                        'adels_titel': mdb.find('NAMEN').find('NAME').find('ADEL').text,
                        'familienstand': fam,
                        'kinder': kinder}
            #print(mdb_data)
            self.insert('mdb', mdb_data)
            return id
        else:
            return res

    def insertMdb_from_rede(self, redner):
        res = self.findMdb(redner.get("id"))
        if not res:
            id = self.getNewId('mdb')
            mdb_data = {'idmdb': id,
                        'bt_id': redner.get("id"),
                        'vorname': redner.find('name').find("vorname").text,
                        'nachname': redner.find('name').find("nachname").text,
                        'geschlecht': None,
                        'titel': None,
                        'geburtsdatum': None,
                        'sterbedatum': None,
                        'adels_titel': None,
                        'familienstand': None}

            self.insert('mdb', mdb_data)
            return id
        else:
            return res

    def findMandat(self, wp, mdb_id):
        if mdb_id is None:
            return None
        query = f"SELECT idmandat FROM mandat WHERE mdb = {mdb_id} AND wahlp = {wp}"
        result = self.query(query)
        if not result:
            return None
        else:
            return result[0]['idmandat']

    def insertWahlperiode(self, wp):
        if wp is None:
            return None
        query = f"SELECT idwahlperiode FROM wahlperiode WHERE idwahlperiode = {wp.find('WP').text}"
        result = self.query(query)
        if not result:
            self.insert('wahlperiode', {'idwahlperiode': int(wp.find('WP').text)})

    def insertMandat(self, wp, mdb_id):

        bundesländer = {'***': None,
                        '**': None,
                        '*': None,
                        'BAD': 'BW',
                        'BAY': 'BY',
                        'BB': 'BB',
                        'BE': 'BE',
                        'BLN': 'BE',
                        'BLW': 'BE',
                        'BRA': 'BB',
                        'BRE': 'HB',
                        'BW': 'BW',
                        'BWG': 'BW',
                        'BY': 'BY',
                        'HB': 'HB',
                        'HBG': 'HH',
                        'HE': 'HE',
                        'HES': 'HE',
                        'HH': 'HH',
                        'MBV': 'MV',
                        'MV': 'MV',
                        'NDS': 'NI',
                        'NI': 'NI',
                        'NRW': 'NRW',
                        'NW': 'NRW',
                        'RP': 'RP',
                        'RPF': 'RP',
                        'SAA': 'SL',
                        'SAC': 'SN',
                        'SH': 'SH',
                        'SL': 'SL',
                        'SLD': 'SL',
                        'SN': 'SN',
                        'ST': 'ST',
                        'SWH': 'SH',
                        'TH': 'TH',
                        'THÜ': 'TH',
                        'WBB': 'BE',
                        'WBH': 'BE'}

        res = self.findMandat(int(wp.find('WP').text), mdb_id)
        if not res:
            id = 0
            max_id = self.getMaxId('mandat')
            if max_id is not None:
                id = max_id + 1
            ins = wp.find('INSTITUTIONEN').findall('INSTITUTION')
            fraktion_lang = None
            fraktion_id = None
            fraktion_kurz = None
            for institut in ins:
                if 'Fraktion/Gruppe' in institut.find('INSART_LANG').text:
                    fraktion_lang = institut.find('INS_LANG').text
                    fraktion_id = self.insertFraktion(fraktion_lang)

            ab = wp.find('MDBWP_VON').text
            bis = wp.find('MDBWP_BIS').text
            data = {'idMandat': id,
                    'ab': datetime.strptime(ab, '%d.%m.%Y') if ab is not None else None,
                    'bis': datetime.strptime(bis, '%d.%m.%Y') if bis is not None else None,
                    'fraktion': fraktion_id,
                    'wahlp': int(wp.find('WP').text),
                    'art': wp.find('MANDATSART').text,
                    'bundesland': bundesländer[wp.find('WKR_LAND').text] if wp.find(
                        'WKR_LAND').text is not None else None,
                    'mdb': mdb_id, }
            self.insert('mandat', data)
            return id
        else:
            return res

    def readStammdaten(self, root):
        mdbs = root.findall('MDB')

        for mdb in tqdm(mdbs, desc='parsing Mandate'):
            mdb_id = self.insertMdb_from_stamm(mdb)
            wahlperioden = mdb.find('WAHLPERIODEN').findall('WAHLPERIODE')
            for wp in wahlperioden:
                self.insertWahlperiode(wp)
                self.insertMandat(wp, mdb_id)

    def currentWahlperiode(self):
        query = "select MAX(idWahlperiode) From wahlperiode"
        return self.query(query)[0]['MAX(idWahlperiode)']

    def insertRolle(self, data):
        self.insert('Rolle', data)

    def findRolle(self, mandatid):
        query = "select * From rolle WHERE mandat = " + str(mandatid)
        result = self.query(query)
        if not result:
            return None
        else:
            return result[0]

    def evalSitzung(self, root, pbar):

        fraktionen_regex = [r'CDU.CSU',
                            r'LINKEN?',
                            r'FDP',
                            r'(Bündnis)?.?(90)?.?(die)?.?(Grünen?)?',
                            r'AfD',
                            r'SPD']
        fraktionen = ['CDU/CSU', 'LINKE', 'FDP', 'GRÜNE', 'AfD', 'SPD']

        sitzungsverlauf = root.find('sitzungsverlauf')
        vorspann = root.find('vorspann')

        sitzung = vorspann.find('kopfdaten').find('plenarprotokoll-nummer')
        datum = vorspann.find('kopfdaten').find('veranstaltungsdaten').find('datum').attrib['date']

        date = datetime.strptime(datum, '%d.%m.%Y')

        query = ("SELECT * FROM sitzung "
                 "WHERE wahlperiode = " + sitzung.find('wahlperiode').text + " "
                 "AND sitzungsnr = " + sitzung.find('sitzungsnr').text)

        sitzung_id = self.getNewId('sitzung')

        self.cursor.execute(query)
        if self.cursor.rowcount < 1:
            self.insert('sitzung', {'sitzungsnr': int(sitzung.find('sitzungsnr').text),
                                    'wahlperiode': int(sitzung.find('wahlperiode').text),
                                    'idsitzung': sitzung_id,
                                    'datum': date})

        tops = []
        inhalt = vorspann.find('inhaltsverzeichnis')
        for tagespunkt in inhalt.findall('ivz-block'):
            nummer = -1
            punkt = tagespunkt.find('ivz-block-titel').text
            if 'ordnungspunkt' in punkt:
                num = re.search(r'\d+', punkt)
                if num is not None:
                    nummer = int(num.group())
                else:  # Roman Numeral
                    num = re.search(r'\s[iIvVxXcCdDlLmM]+', punkt)
                    nummer = roman_to_int(num.group())
            else:
                break
            thema = ''
            for eintrag in tagespunkt.findall('ivz-eintrag'):
                t = eintrag.find('ivz-eintrag-inhalt').text
                if t is not None:
                    if len(thema) > 0:
                        thema += '\n'
                    thema += t

            search = re.search(r'Befragung der Bundesregierung', thema)

            data = {'idTagesordnungspunkt': self.getNewId('tagesordnungspunkt'),
                    'nummer': nummer,
                    'thema': thema,
                    'sitzung': sitzung_id,
                    'zusatztagespunkt': 1 if 'Zusatz' in tagespunkt.find('ivz-block-titel').text else 0,
                    'befragung': 1 if search is not None else 0}
            tops += [data]
            self.insert('tagesordnungspunkt', data)

        for tp in sitzungsverlauf.findall('tagesordnungspunkt'):
            frage = False
            for p_1 in tp.findall('p'):
                if p_1.attrib == {'klasse': 'T_NaS'} or p_1.attrib == {'klasse': 'T_Fett'}:
                    if p_1.text is None:
                        continue
                    pbar.write(p_1.text)
                    if ('fragestunde' in p_1.text.lower()) or ('befragung der bundesregierung' in p_1.text.lower()):
                        frage = True
                        break
            if frage:
                continue
            top_id = None
            num = re.search(r'\d+', tp.attrib['top-id'])
            nummer = 0
            if num is None:
                pbar.write(tp.attrib['top-id'])
            else:
                nummer = int(num.group())
            for top in tops:
                if top['zusatztagespunkt'] == (1 if 'Zusatz' in tp.attrib['top-id'] else 0):
                    if top['nummer'] == nummer:
                        top_id = top['idTagesordnungspunkt']
                        break

            frager_id = None
            kurzintervention_angemeldet = False
            id_rede = None
            for rede in tp.findall('rede'):  # Rede fängt an

                ####### Bundestags(vize)präsi spricht ab hier
                # <name>Vizepräsidentin Petra Pau:</name>
                ####### BPräsi erteilt das Wort an jmd für eine Kurzintervention (Frage nach der Ansprache eines Abgeordneten)
                # <p klasse="J_1">Ist das die Anmeldung einer Kurzintervention, oder wie darf ich das verstehen?</p>
                # <kommentar>(Pia Zimmermann [DIE LINKE]: Ja!)</kommentar>
                # <p klasse="O">– Gut. Ich bitte, das beim nächsten Mal etwas früher zu tun.</p>

                last_id_rede = id_rede

                absatz_data = None
                id_rede = int(rede.attrib['id'][2:])
                redner_fraktion = ''
                btpraesi_redet = False
                abgegeordneter_redet = False
                erster_redner_id = None

                for element in rede:
                    if element.tag == 'name':
                        btpraesi_redet = True
                        abgegeordneter_redet = False
                    elif element.tag == 'p' and element.attrib == {'klasse': 'redner'}:
                        redner = element.find('redner')
                        name = redner.find('name')
                        abgegeordneter_redet = True
                        btpraesi_redet = False
                        try:
                            redner_fraktion = name.find('fraktion').text
                        except AttributeError:
                            redner_fraktion = 'fraktionslos'

                        for regex, fraktion in zip(fraktionen_regex, fraktionen):
                            match = re.search(regex, redner_fraktion, re.I | re.S)
                            if match:
                                redner_fraktion = fraktion

                        redner_now = self.insertMdb_from_rede(redner)

                        if erster_redner_id is None:
                            erster_redner_id = redner_now

                        if erster_redner_id == redner_now:
                            frager_id = None
                        else:
                            frager_id = redner_now

                        last_rede_data = self.getRede(last_id_rede)

                        rolle = element.find('redner').find('name').find('rolle')
                        idRolle = None
                        if rolle is not None and frager_id is None:
                            mandatid = self.findMandat(self.currentWahlperiode(), erster_redner_id)
                            if mandatid is not None and self.findRolle(mandatid) is None:
                                idRolle = self.getNewId('rolle')
                                data = {'idRolle': idRolle,
                                        'Rolle_kurz': rolle.find('rolle_kurz').text,
                                        'Rolle_lang': rolle.find('rolle_lang').text,
                                        'mandat': self.findMandat(self.currentWahlperiode(), erster_redner_id)}
                                self.insertRolle(data)

                        self.insertRede(id_rede,
                                        erster_redner_id,
                                        top_id,
                                        last_id_rede if kurzintervention_angemeldet else None,
                                        last_rede_data[0]['kurzintervention'],
                                        idRolle)



                        kurzintervention_angemeldet = False

                    # TODO: Fragen von andern mdb müssen noch erfasst werden
                    elif element.tag == 'p' and element.attrib != {'klasse': 'redner'}:  # Gesprochener Text
                        if btpraesi_redet:
                            if 'kurzintervention' in element.text.lower():
                                kurzintervention_angemeldet = True
                        else:
                            # self.insertRede(id_rede, redner, top_id)
                            absatz_data = {'idabsatz': self.getNewId('absatz'),
                                           'text': element.text,
                                           'frage_von': frager_id,  # Frage eines anderen mdb
                                           'rede': id_rede}

                            self.insert('absatz', absatz_data)
                            # frager_id = None

                    elif element.tag == 'kommentar':
                        # TODO: Kommentare von anderen Bundetagsabgeordneten aufnehmen
                        if abgegeordneter_redet:
                            kommentar = element.text.split('sowie')
                            if 'Beifall' in kommentar[0]:
                                for regex, fraktion in zip(fraktionen_regex, fraktionen):
                                    match = re.search(regex, kommentar[0], re.I | re.S)
                                    if match:
                                        frak_id_von = self.insertFraktion(fraktion)
                                        beifall_id = self.getNewId('Beifall')
                                        frak_id_fuer = self.findFraktion(redner_fraktion)
                                        if frak_id_fuer is None:
                                            frak_id_fuer = self.insertFraktion(redner_fraktion)
                                            #raise ValueError(f"findFraktion // Didn't find id for fraktion -> {redner_fraktion}")

                                        beifall_data = {'idbeifall': beifall_id,
                                                        'von': frak_id_von,
                                                        'für': frak_id_fuer,
                                                        'alle': 1,
                                                        'absatz': absatz_data['idabsatz']}
                                        self.insert('Beifall', beifall_data)

                            if len(kommentar) > 1:
                                wenigerBeifall = kommentar[1].split('–')
                                for regex, fraktion in zip(fraktionen_regex, fraktionen):
                                    match = re.search(regex, wenigerBeifall[0], re.I | re.S)
                                    if match:
                                        beifall_id = self.getNewId('Beifall')
                                        self.insert('Beifall',
                                                    {'idbeifall': beifall_id,
                                                     'von': self.insertFraktion(fraktion),
                                                     'für': self.getIdByName('fraktion', 'name_kurz', redner_fraktion),
                                                     'alle': 0,
                                                     'absatz': absatz_data['idabsatz']})

