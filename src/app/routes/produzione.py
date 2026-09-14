import statistics

from flask import Blueprint, jsonify

from ..db import execute_query, execute_single_query

produzione_bp = Blueprint("produzione", __name__)


@produzione_bp.route("/produzione-media-mensile")
def produzione_media_mensile():

    query = """
        SELECT
            f.nome AS fonte,
            MONTH(p.data) AS mese,
            ROUND(AVG(p.generazione), 2) AS produzione_media
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND p.generazione IS NOT NULL
        GROUP BY
            f.nome,
            MONTH(p.data)
        ORDER BY
            f.nome,
            mese
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        fonte = riga["fonte"]

        if fonte not in risultato:
            risultato[fonte] = []

        risultato[fonte].append({
            "mese": riga["mese"],
            "produzione_media": riga["produzione_media"]
        })

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di produzione per il 2025."
        })

    return jsonify(risultato)


@produzione_bp.route("/percentuale-produzione-fonte")
def percentuale_produzione_fonte():

    query = """
        SELECT
            f.nome AS fonte,
            SUM(p.generazione) AS produzione_totale
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND p.generazione IS NOT NULL
        GROUP BY
            f.nome
        ORDER BY
            produzione_totale DESC
    """

    dati = execute_query(query)

    if not dati:
        return jsonify({
            "errore": "Non sono presenti dati di produzione per il 2025."
        })

    produzione_totale = sum(
        float(riga["produzione_totale"]) for riga in dati
    )

    risultato = []

    for riga in dati:

        fonte = riga["fonte"]
        produzione = float(riga["produzione_totale"])
        percentuale = (produzione / produzione_totale) * 100

        risultato.append({
            "fonte": fonte,
            "produzione_totale": round(produzione, 2),
            "percentuale_produzione": round(percentuale, 2)
        })

    return jsonify(risultato)


@produzione_bp.route("/produzione-rinnovabile-non-rinnovabile")
def produzione_rinnovabile_non_rinnovabile():

    query = """
        SELECT
            CASE
                WHEN f.rinnovabile = 'si'
                    THEN 'rinnovabile'
                ELSE 'non rinnovabile'
            END AS tipo,
            SUM(p.generazione) AS produzione_totale
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND p.generazione IS NOT NULL
        GROUP BY
            CASE
                WHEN f.rinnovabile = 'si'
                    THEN 'rinnovabile'
                ELSE 'non rinnovabile'
            END
        ORDER BY
            produzione_totale DESC
    """

    dati = execute_query(query)

    if not dati:
        return jsonify({
            "errore": "Non sono presenti dati di produzione per il 2025."
        })

    produzione_totale = sum(
        float(riga["produzione_totale"]) for riga in dati
    )

    risultato = []

    for riga in dati:

        tipo = riga["tipo"]
        produzione = float(riga["produzione_totale"])
        percentuale = (produzione / produzione_totale) * 100

        risultato.append({
            "tipo": tipo,
            "produzione_totale": round(produzione, 2),
            "percentuale_produzione": round(percentuale, 2)
        })

    return jsonify(risultato)


def _fascia_produzione_3_ore(fonte_nome):

    query = """
        SELECT
            HOUR(p.orario) AS ora,
            AVG(p.generazione) AS produzione_media
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND f.nome = %s
          AND p.generazione IS NOT NULL
        GROUP BY
            HOUR(p.orario)
        ORDER BY
            ora
    """

    dati = execute_query(query, [fonte_nome])

    if len(dati) < 3:
        return {
            "errore": "Non ci sono abbastanza dati per calcolare una fascia di 3 ore."
        }

    produzione_oraria = {
        int(riga["ora"]): float(riga["produzione_media"])
        for riga in dati
    }

    fasce = []

    for ora in range(0, 22):

        if (
            ora in produzione_oraria
            and ora + 1 in produzione_oraria
            and ora + 2 in produzione_oraria
        ):

            media_fascia = (
                produzione_oraria[ora]
                + produzione_oraria[ora + 1]
                + produzione_oraria[ora + 2]
            ) / 3

            fasce.append({
                "ora_inizio": ora,
                "ora_fine": ora + 2,
                "produzione_media": media_fascia
            })

    if not fasce:
        return {
            "errore": "Non sono state trovate fasce di 3 ore valide."
        }

    fascia_massima = max(fasce, key=lambda fascia: fascia["produzione_media"])
    fascia_minima = min(fasce, key=lambda fascia: fascia["produzione_media"])

    return {
        "fascia_3_ore_piu_produttiva": {
            "dalle": f"{fascia_massima['ora_inizio']:02d}:00",
            "alle": f"{fascia_massima['ora_fine'] + 1:02d}:00",
            "produzione_media": round(fascia_massima["produzione_media"], 2)
        },
        "fascia_3_ore_meno_produttiva": {
            "dalle": f"{fascia_minima['ora_inizio']:02d}:00",
            "alle": f"{fascia_minima['ora_fine'] + 1:02d}:00",
            "produzione_media": round(fascia_minima["produzione_media"], 2)
        }
    }


def _giorno_mese_massima_produzione(fonte_nome):

    query_giorno = """
        SELECT
            p.data,
            AVG(p.generazione) AS produzione_media
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND f.nome = %s
          AND p.generazione IS NOT NULL
        GROUP BY
            p.data
        ORDER BY
            produzione_media DESC
        LIMIT 1
    """

    query_mese = """
        SELECT
            MONTH(p.data) AS mese,
            AVG(p.generazione) AS produzione_media
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND f.nome = %s
          AND p.generazione IS NOT NULL
        GROUP BY
            MONTH(p.data)
        ORDER BY
            produzione_media DESC
        LIMIT 1
    """

    giorno = execute_single_query(query_giorno, [fonte_nome])
    mese = execute_single_query(query_mese, [fonte_nome])

    if giorno is None or mese is None:
        return {
            "errore": f"Non sono presenti dati di produzione {fonte_nome} per il 2025."
        }

    return {
        "giorno_massima_produzione_media": {
            "data": giorno["data"],
            "produzione_media": round(float(giorno["produzione_media"]), 2)
        },
        "mese_massima_produzione_media": {
            "mese": mese["mese"],
            "produzione_media": round(float(mese["produzione_media"]), 2)
        }
    }


@produzione_bp.route("/fascia-produzione-solare-3-ore")
def fascia_produzione_solare_3_ore():
    return jsonify(_fascia_produzione_3_ore("Photovoltaic"))


@produzione_bp.route("/massima-produzione-media-fotovoltaica")
def massima_produzione_media_fotovoltaica():
    return jsonify(_giorno_mese_massima_produzione("Photovoltaic"))


@produzione_bp.route("/fascia-produzione-eolica-3-ore")
def fascia_produzione_eolica_3_ore():
    return jsonify(_fascia_produzione_3_ore("Wind"))


@produzione_bp.route("/massima-produzione-media-eolica")
def massima_produzione_media_eolica():
    return jsonify(_giorno_mese_massima_produzione("Wind"))


@produzione_bp.route("/mese-massima-produzione-idroelettrica")
def mese_massima_produzione_idroelettrica():

    query = """
        SELECT
            MONTH(p.data) AS mese,
            AVG(p.generazione) AS produzione_media
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND f.nome = 'Hydro'
          AND p.generazione IS NOT NULL
        GROUP BY
            MONTH(p.data)
        ORDER BY
            produzione_media DESC
        LIMIT 1
    """

    risultato = execute_single_query(query)

    if risultato is None:
        return jsonify({
            "errore": "Non sono presenti dati di produzione idroelettrica per il 2025."
        })

    return jsonify({
        "mese_massima_produzione_media": {
            "mese": risultato["mese"],
            "produzione_media": round(float(risultato["produzione_media"]), 2)
        }
    })


@produzione_bp.route("/volatilita-produzione-fonte")
def volatilita_produzione_fonte():

    query = """
        SELECT
            f.nome AS fonte,
            p.data,
            AVG(p.generazione) AS produzione_media_giornaliera
        FROM produzioni AS p
        JOIN fonti_energetiche AS f
            ON p.fonte_id = f.id
        WHERE YEAR(p.data) = 2025
          AND p.generazione IS NOT NULL
        GROUP BY
            f.nome,
            p.data
        ORDER BY
            f.nome,
            p.data
    """

    dati = execute_query(query)

    if not dati:
        return jsonify({
            "errore": "Non sono presenti dati di produzione per il 2025."
        })

    produzioni_per_fonte = {}

    for riga in dati:

        fonte = riga["fonte"]
        produzione = float(riga["produzione_media_giornaliera"])

        if fonte not in produzioni_per_fonte:
            produzioni_per_fonte[fonte] = []

        produzioni_per_fonte[fonte].append(produzione)

    risultato = []

    for fonte, produzioni in produzioni_per_fonte.items():

        media = statistics.mean(produzioni)
        deviazione_standard = statistics.pstdev(produzioni)

        if media == 0:
            volatilita = 0
        else:
            volatilita = (deviazione_standard / media) * 100

        risultato.append({
            "fonte": fonte,
            "produzione_media": round(media, 2),
            "deviazione_standard": round(deviazione_standard, 2),
            "volatilita_percentuale": round(volatilita, 2)
        })

    risultato.sort(key=lambda x: x["volatilita_percentuale"], reverse=True)

    return jsonify(risultato)
