from flask import Blueprint, jsonify, request

from ..db import execute_query
from ..utils import handle_error

incroci_bp = Blueprint("incroci", __name__)


def _anno_valido(anno_str):

    try:
        anno_int = int(anno_str)

        if anno_int < 1900 or anno_int > 2100:
            raise ValueError

        return anno_int

    except ValueError:
        return None


@incroci_bp.route("/temperatura-errore-previsione-domanda")
def temperatura_errore_previsione_domanda():

    anno = request.args.get("anno", default="2025")
    zona = request.args.get("zona")

    anno_int = _anno_valido(anno)

    if anno_int is None:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query = """
        WITH temperatura_giornaliera AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            INNER JOIN province p
                ON m.provincia_id = p.id
            INNER JOIN regioni r
                ON p.regione_id = r.id
            INNER JOIN bidding_zones z
                ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s
            GROUP BY
                z.id, z.nome, m.data
        ),

        temperatura_classificata AS (
            SELECT
                zona_id, zona, data, temperatura_media,
                NTILE(10) OVER (
                    PARTITION BY zona_id
                    ORDER BY temperatura_media
                ) AS decile_temperatura
            FROM temperatura_giornaliera
        ),

        domanda_giornaliera AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                d.data,
                AVG(d.domanda_effettiva) AS domanda_effettiva,
                AVG(d.domanda_prevista) AS domanda_prevista,
                AVG(ABS(d.domanda_effettiva - d.domanda_prevista))
                    AS errore_assoluto
            FROM domande d
            INNER JOIN bidding_zones z
                ON d.zona_id = z.id
            WHERE YEAR(d.data) = %s
            GROUP BY
                z.id, z.nome, d.data
        ),

        dati_completi AS (
            SELECT
                t.zona_id, t.zona, t.data,
                t.temperatura_media, t.decile_temperatura,
                d.domanda_effettiva, d.domanda_prevista, d.errore_assoluto,
                CASE
                    WHEN t.decile_temperatura = 1 THEN 'freddo_estremo'
                    WHEN t.decile_temperatura = 10 THEN 'caldo_estremo'
                    ELSE 'normale'
                END AS tipo_periodo
            FROM temperatura_classificata t
            INNER JOIN domanda_giornaliera d
                ON t.zona_id = d.zona_id
               AND t.data = d.data
        )

        SELECT
            zona,
            tipo_periodo,
            COUNT(*) AS numero_giorni,
            ROUND(AVG(temperatura_media), 2) AS temperatura_media,
            ROUND(MIN(temperatura_media), 2) AS temperatura_minima,
            ROUND(MAX(temperatura_media), 2) AS temperatura_massima,
            ROUND(AVG(domanda_effettiva), 2) AS domanda_effettiva_media,
            ROUND(AVG(domanda_prevista), 2) AS domanda_prevista_media,
            ROUND(AVG(errore_assoluto), 2) AS errore_medio,
            ROUND(
                AVG(
                    errore_assoluto
                    / NULLIF(ABS(domanda_effettiva), 0)
                    * 100
                ),
                2
            ) AS errore_percentuale_medio

        FROM dati_completi
    """

    parametri = [anno_int, anno_int]

    if zona:
        query += " WHERE zona = %s"
        parametri.append(zona)

    query += """
        GROUP BY zona, tipo_periodo
        ORDER BY
            zona,
            CASE tipo_periodo
                WHEN 'freddo_estremo' THEN 1
                WHEN 'normale' THEN 2
                WHEN 'caldo_estremo' THEN 3
            END
    """

    try:
        risultati = execute_query(query, parametri)

        dati = [
            {
                "zona": riga["zona"],
                "tipo_periodo": riga["tipo_periodo"],
                "numero_giorni": int(riga["numero_giorni"]),
                "temperatura_media": float(riga["temperatura_media"]),
                "temperatura_minima": float(riga["temperatura_minima"]),
                "temperatura_massima": float(riga["temperatura_massima"]),
                "domanda_effettiva_media": float(riga["domanda_effettiva_media"]),
                "domanda_prevista_media": float(riga["domanda_prevista_media"]),
                "errore_medio": float(riga["errore_medio"]),
                "errore_percentuale_medio": float(riga["errore_percentuale_medio"])
            }
            for riga in risultati
        ]

        return jsonify({
            "anno": anno_int,
            "zona": zona,

            "domanda_analisi":
                "Nei periodi meteorologicamente estremi "
                "Terna sbaglia di più la previsione?",

            "criterio_classificazione": {
                "freddo_estremo": "10% delle giornate con temperatura più bassa",
                "normale": "80% delle giornate intermedie",
                "caldo_estremo": "10% delle giornate con temperatura più alta"
            },

            "metrica_errore":
                "Errore assoluto medio = "
                "|domanda_effettiva - domanda_prevista|",

            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


@incroci_bp.route("/vento-produzione-eolica")
def vento_produzione_eolica():

    anno = request.args.get("anno", default="2025")
    zona = request.args.get("zona")

    anno_int = _anno_valido(anno)

    if anno_int is None:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query = """
        WITH vento_orario AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data,
                m.orario,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            INNER JOIN province p
                ON m.provincia_id = p.id
            INNER JOIN regioni r
                ON p.regione_id = r.id
            INNER JOIN bidding_zones z
                ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s
            GROUP BY
                z.id, z.nome, m.data, m.orario
        ),

        produzione_eolica AS (
            SELECT
                p.data,
                p.orario,
                SUM(p.generazione) AS produzione_eolica
            FROM produzioni p
            INNER JOIN fonti_energetiche f
                ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s
              AND LOWER(f.nome) LIKE '%%eolic%%'
            GROUP BY
                p.data, p.orario
        ),

        dati_completi AS (
            SELECT
                v.zona_id, v.zona, v.data, v.orario,
                v.vento_medio, e.produzione_eolica,
                CASE
                    WHEN v.vento_medio < 2 THEN 'vento_molto_debole'
                    WHEN v.vento_medio < 4 THEN 'vento_debole'
                    WHEN v.vento_medio < 6 THEN 'vento_moderato'
                    WHEN v.vento_medio < 8 THEN 'vento_forte'
                    ELSE 'vento_molto_forte'
                END AS fascia_vento
            FROM vento_orario v
            INNER JOIN produzione_eolica e
                ON v.data = e.data
               AND v.orario = e.orario
        )

        SELECT
            zona,
            fascia_vento,
            COUNT(*) AS numero_osservazioni,
            ROUND(AVG(vento_medio), 2) AS vento_medio,
            ROUND(MIN(vento_medio), 2) AS vento_minimo,
            ROUND(MAX(vento_medio), 2) AS vento_massimo,
            ROUND(AVG(produzione_eolica), 2) AS produzione_eolica_media,
            ROUND(MAX(produzione_eolica), 2) AS produzione_eolica_massima,
            ROUND(STDDEV(produzione_eolica), 2) AS deviazione_standard_produzione

        FROM dati_completi
    """

    parametri = [anno_int, anno_int]

    if zona:
        query += " WHERE zona = %s"
        parametri.append(zona)

    query += """
        GROUP BY zona, fascia_vento
        ORDER BY
            zona,
            CASE fascia_vento
                WHEN 'vento_molto_debole' THEN 1
                WHEN 'vento_debole' THEN 2
                WHEN 'vento_moderato' THEN 3
                WHEN 'vento_forte' THEN 4
                WHEN 'vento_molto_forte' THEN 5
            END
    """

    try:
        risultati = execute_query(query, parametri)

        dati = [
            {
                "zona": riga["zona"],
                "fascia_vento": riga["fascia_vento"],
                "numero_osservazioni": int(riga["numero_osservazioni"]),
                "vento_medio": float(riga["vento_medio"]),
                "vento_minimo": float(riga["vento_minimo"]),
                "vento_massimo": float(riga["vento_massimo"]),
                "produzione_eolica_media": float(riga["produzione_eolica_media"]),
                "produzione_eolica_massima": float(riga["produzione_eolica_massima"]),
                "deviazione_standard_produzione":
                    float(riga["deviazione_standard_produzione"])
            }
            for riga in risultati
        ]

        return jsonify({
            "anno": anno_int,
            "zona": zona,

            "domanda_analisi":
                "Come varia la produzione eolica "
                "al variare del vento considerando "
                "la natura non lineare della relazione?",

            "criterio_analisi":
                "Il vento è suddiviso in fasce climatiche "
                "per evitare di assumere una relazione lineare.",

            "fasce_vento": {
                "vento_molto_debole": "vento < 2",
                "vento_debole": "2 <= vento < 4",
                "vento_moderato": "4 <= vento < 6",
                "vento_forte": "6 <= vento < 8",
                "vento_molto_forte": "vento >= 8"
            },

            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


@incroci_bp.route("/indice-solare-produzione-fotovoltaica")
def indice_solare_produzione_fotovoltaica():

    anno = request.args.get("anno", default="2025")

    anno_int = _anno_valido(anno)

    if anno_int is None:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query = """
        WITH radiazione_provincia AS (
            SELECT
                m.data, m.provincia_id,
                AVG(m.radiazione) AS radiazione_media
            FROM meteo m
            WHERE YEAR(m.data) = %s
            GROUP BY m.data, m.provincia_id
        ),

        radiazione_mensile AS (
            SELECT
                YEAR(r.data) AS anno,
                MONTH(r.data) AS mese,
                r.provincia_id,
                AVG(r.radiazione_media) AS radiazione_media
            FROM radiazione_provincia r
            GROUP BY YEAR(r.data), MONTH(r.data), r.provincia_id
        ),

        capacita_fotovoltaica AS (
            SELECT
                c.anno, c.mese, c.provincia_id,
                SUM(c.potenza_nominale) AS capacita_fv
            FROM capacita_installate c
            INNER JOIN fonti_energetiche f
                ON c.fonte_id = f.id
            WHERE c.anno = %s
              AND LOWER(f.nome) LIKE '%%fotovoltaic%%'
            GROUP BY c.anno, c.mese, c.provincia_id
        ),

        indice_solare AS (
            SELECT
                r.anno, r.mese,
                SUM(r.radiazione_media * c.capacita_fv)
                    / NULLIF(SUM(c.capacita_fv), 0)
                    AS indice_solare_nazionale,
                SUM(c.capacita_fv) AS capacita_fv_nazionale
            FROM radiazione_mensile r
            INNER JOIN capacita_fotovoltaica c
                ON r.anno = c.anno
               AND r.mese = c.mese
               AND r.provincia_id = c.provincia_id
            GROUP BY r.anno, r.mese
        ),

        produzione_fotovoltaica AS (
            SELECT
                YEAR(p.data) AS anno,
                MONTH(p.data) AS mese,
                SUM(p.generazione) AS produzione_fv
            FROM produzioni p
            INNER JOIN fonti_energetiche f
                ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s
              AND LOWER(f.nome) LIKE '%%fotovoltaic%%'
            GROUP BY YEAR(p.data), MONTH(p.data)
        )

        SELECT
            i.anno, i.mese,
            ROUND(i.indice_solare_nazionale, 4) AS indice_solare_nazionale,
            ROUND(i.capacita_fv_nazionale, 2) AS capacita_fv_nazionale,
            ROUND(p.produzione_fv, 2) AS produzione_fotovoltaica,
            ROUND(
                p.produzione_fv / NULLIF(i.capacita_fv_nazionale, 0),
                6
            ) AS produzione_specifica

        FROM indice_solare i
        INNER JOIN produzione_fotovoltaica p
            ON i.anno = p.anno
           AND i.mese = p.mese
        ORDER BY i.anno, i.mese
    """

    parametri = [anno_int, anno_int, anno_int]

    try:
        risultati = execute_query(query, parametri)

        dati = [
            {
                "anno": int(riga["anno"]),
                "mese": int(riga["mese"]),
                "indice_solare_nazionale": float(riga["indice_solare_nazionale"]),
                "capacita_fv_nazionale": float(riga["capacita_fv_nazionale"]),
                "produzione_fotovoltaica": float(riga["produzione_fotovoltaica"]),
                "produzione_specifica": float(riga["produzione_specifica"])
            }
            for riga in risultati
        ]

        correlazione = None

        if len(dati) >= 2:

            x = [r["indice_solare_nazionale"] for r in dati]
            y = [r["produzione_specifica"] for r in dati]

            media_x = sum(x) / len(x)
            media_y = sum(y) / len(y)

            numeratore = sum(
                (x[i] - media_x) * (y[i] - media_y)
                for i in range(len(x))
            )

            denominatore_x = sum((v - media_x) ** 2 for v in x)
            denominatore_y = sum((v - media_y) ** 2 for v in y)
            denominatore = (denominatore_x * denominatore_y) ** 0.5

            if denominatore != 0:
                correlazione = numeratore / denominatore

        return jsonify({
            "anno": anno_int,

            "domanda_analisi":
                "Quanto l'irraggiamento solare "
                "influenza la produzione fotovoltaica "
                "tenendo conto della capacità installata?",

            "metodologia":
                "L'indice solare nazionale è calcolato "
                "come media ponderata della radiazione "
                "provinciale utilizzando la capacità "
                "fotovoltaica installata come peso.",

            "formula_indice_solare":
                "SUM(radiazione * capacita_fv) / SUM(capacita_fv)",

            "produzione_specifica":
                "produzione fotovoltaica / capacità fotovoltaica installata",

            "correlazione_pearson":
                None if correlazione is None else round(correlazione, 4),

            "numero_mesi": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


@incroci_bp.route("/domanda-per-fasce-temperatura")
def domanda_per_fasce_temperatura():

    anno = request.args.get("anno", default="2025")
    zona = request.args.get("zona")

    anno_int = _anno_valido(anno)

    if anno_int is None:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query = """
        WITH temperatura_oraria AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data, m.orario,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            INNER JOIN province p
                ON m.provincia_id = p.id
            INNER JOIN regioni r
                ON p.regione_id = r.id
            INNER JOIN bidding_zones z
                ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s
            GROUP BY
                z.id, z.nome, m.data, m.orario
        ),

        domanda_oraria AS (
            SELECT
                d.zona_id, d.data, d.orario,
                AVG(d.domanda_effettiva) AS domanda_effettiva,
                AVG(d.domanda_prevista) AS domanda_prevista
            FROM domande d
            WHERE YEAR(d.data) = %s
            GROUP BY
                d.zona_id, d.data, d.orario
        ),

        dati_completi AS (
            SELECT
                t.zona_id, t.zona, t.data, t.orario,
                t.temperatura_media,
                d.domanda_effettiva, d.domanda_prevista,
                CASE
                    WHEN t.temperatura_media < -5 THEN 'sotto_-5'
                    WHEN t.temperatura_media < 0 THEN '-5_0'
                    WHEN t.temperatura_media < 5 THEN '0_5'
                    WHEN t.temperatura_media < 10 THEN '5_10'
                    WHEN t.temperatura_media < 15 THEN '10_15'
                    WHEN t.temperatura_media < 20 THEN '15_20'
                    WHEN t.temperatura_media < 25 THEN '20_25'
                    WHEN t.temperatura_media < 30 THEN '25_30'
                    ELSE 'sopra_30'
                END AS fascia_temperatura
            FROM temperatura_oraria t
            INNER JOIN domanda_oraria d
                ON t.zona_id = d.zona_id
               AND t.data = d.data
               AND t.orario = d.orario
        )

        SELECT
            zona,
            fascia_temperatura,
            COUNT(*) AS numero_osservazioni,
            ROUND(MIN(temperatura_media), 2) AS temperatura_minima,
            ROUND(MAX(temperatura_media), 2) AS temperatura_massima,
            ROUND(AVG(temperatura_media), 2) AS temperatura_media,
            ROUND(AVG(domanda_effettiva), 2) AS domanda_effettiva_media,
            ROUND(MAX(domanda_effettiva), 2) AS domanda_effettiva_massima,
            ROUND(MIN(domanda_effettiva), 2) AS domanda_effettiva_minima,
            ROUND(AVG(domanda_prevista), 2) AS domanda_prevista_media

        FROM dati_completi
    """

    parametri = [anno_int, anno_int]

    if zona:
        query += " WHERE zona = %s"
        parametri.append(zona)

    query += """
        GROUP BY zona, fascia_temperatura
        ORDER BY
            zona,
            CASE fascia_temperatura
                WHEN 'sotto_-5' THEN 1
                WHEN '-5_0' THEN 2
                WHEN '0_5' THEN 3
                WHEN '5_10' THEN 4
                WHEN '10_15' THEN 5
                WHEN '15_20' THEN 6
                WHEN '20_25' THEN 7
                WHEN '25_30' THEN 8
                WHEN 'sopra_30' THEN 9
            END
    """

    try:
        risultati = execute_query(query, parametri)

        dati = [
            {
                "zona": riga["zona"],
                "fascia_temperatura": riga["fascia_temperatura"],
                "numero_osservazioni": int(riga["numero_osservazioni"]),
                "temperatura_minima": float(riga["temperatura_minima"]),
                "temperatura_massima": float(riga["temperatura_massima"]),
                "temperatura_media": float(riga["temperatura_media"]),
                "domanda_effettiva_media": float(riga["domanda_effettiva_media"]),
                "domanda_effettiva_massima": float(riga["domanda_effettiva_massima"]),
                "domanda_effettiva_minima": float(riga["domanda_effettiva_minima"]),
                "domanda_prevista_media": float(riga["domanda_prevista_media"])
            }
            for riga in risultati
        ]

        return jsonify({
            "anno": anno_int,
            "zona": zona,

            "domanda_analisi":
                "Come varia la domanda elettrica "
                "nelle diverse fasce di temperatura?",

            "criterio_classificazione": {
                "sotto_-5": "temperatura < -5 °C",
                "-5_0": "-5 °C <= temperatura < 0 °C",
                "0_5": "0 °C <= temperatura < 5 °C",
                "5_10": "5 °C <= temperatura < 10 °C",
                "10_15": "10 °C <= temperatura < 15 °C",
                "15_20": "15 °C <= temperatura < 20 °C",
                "20_25": "20 °C <= temperatura < 25 °C",
                "25_30": "25 °C <= temperatura < 30 °C",
                "sopra_30": "temperatura >= 30 °C"
            },

            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


@incroci_bp.route("/correlazione-temperatura-domanda")
def correlazione_temperatura_domanda():

    anno = request.args.get("anno", default="2025")
    zona = request.args.get("zona")

    anno_int = _anno_valido(anno)

    if anno_int is None:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query_dettaglio = """
        WITH popolazione_provincia AS (
            SELECT provincia_id, popolazione
            FROM dati_province
            WHERE anno = %s
        ),

        temperatura_provincia AS (
            SELECT
                m.data, m.orario, m.provincia_id,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            WHERE YEAR(m.data) = %s
            GROUP BY m.data, m.orario, m.provincia_id
        ),

        temperatura_zona AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                t.data, t.orario,
                SUM(t.temperatura_media * pp.popolazione)
                    / NULLIF(SUM(pp.popolazione), 0)
                    AS temperatura_pesata
            FROM temperatura_provincia t
            INNER JOIN popolazione_provincia pp
                ON t.provincia_id = pp.provincia_id
            INNER JOIN province p
                ON t.provincia_id = p.id
            INNER JOIN regioni r
                ON p.regione_id = r.id
            INNER JOIN bidding_zones z
                ON r.zona_id = z.id
            GROUP BY z.id, z.nome, t.data, t.orario
        ),

        domanda_zona AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                d.data, d.orario,
                AVG(d.domanda_effettiva) AS domanda_effettiva
            FROM domande d
            INNER JOIN bidding_zones z
                ON d.zona_id = z.id
            WHERE YEAR(d.data) = %s
            GROUP BY z.id, z.nome, d.data, d.orario
        )

        SELECT
            t.zona,
            t.temperatura_pesata,
            d.domanda_effettiva
        FROM temperatura_zona t
        INNER JOIN domanda_zona d
            ON t.zona_id = d.zona_id
           AND t.data = d.data
           AND t.orario = d.orario
    """

    parametri_dettaglio = [anno_int, anno_int, anno_int]

    if zona:
        query_dettaglio += " WHERE t.zona = %s"
        parametri_dettaglio.append(zona)

    try:
        osservazioni = execute_query(query_dettaglio, parametri_dettaglio)

        zone = {}

        for riga in osservazioni:

            nome_zona = riga["zona"]

            if nome_zona not in zone:
                zone[nome_zona] = {"temperature": [], "domande": []}

            zone[nome_zona]["temperature"].append(float(riga["temperatura_pesata"]))
            zone[nome_zona]["domande"].append(float(riga["domanda_effettiva"]))

        dati = []

        for nome_zona, valori in zone.items():

            temperature = valori["temperature"]
            domande = valori["domande"]

            n = len(temperature)

            if n < 2:
                correlazione = None
            else:

                media_t = sum(temperature) / n
                media_d = sum(domande) / n

                numeratore = sum(
                    (temperature[i] - media_t) * (domande[i] - media_d)
                    for i in range(n)
                )

                denominatore_t = sum((t - media_t) ** 2 for t in temperature)
                denominatore_d = sum((d - media_d) ** 2 for d in domande)
                denominatore = (denominatore_t * denominatore_d) ** 0.5

                correlazione = (
                    None if denominatore == 0
                    else numeratore / denominatore
                )

            temperatura_media = sum(temperature) / n if n > 0 else None
            domanda_media = sum(domande) / n if n > 0 else None

            dati.append({
                "zona": nome_zona,
                "numero_osservazioni": n,

                "temperatura_media_pesata":
                    round(temperatura_media, 2)
                    if temperatura_media is not None else None,

                "domanda_media":
                    round(domanda_media, 2)
                    if domanda_media is not None else None,

                "correlazione_pearson":
                    round(correlazione, 4)
                    if correlazione is not None else None
            })

        return jsonify({
            "anno": anno_int,
            "zona": zona,

            "domanda_analisi":
                "Quanto è correlata la temperatura "
                "alla domanda elettrica nelle "
                "diverse bidding zone?",

            "metodologia":
                "Le province vengono aggregate nella "
                "rispettiva bidding zone e la temperatura "
                "viene pesata in base alla popolazione "
                "provinciale.",

            "formula_temperatura_pesata":
                "SUM(temperatura_provincia * popolazione) / SUM(popolazione)",

            "metrica":
                "Correlazione di Pearson tra temperatura "
                "media pesata e domanda elettrica effettiva.",

            "interpretazione":
                "Un valore positivo indica che la domanda "
                "tende ad aumentare con la temperatura; "
                "un valore negativo indica che tende a "
                "diminuire. Un valore vicino a zero indica "
                "una relazione lineare debole.",

            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)
