import statistics

from flask import Blueprint, jsonify, request

from ..db import execute_query, execute_single_query
from ..utils import get_year_range, handle_error

domanda_bp = Blueprint("domanda", __name__)


# ============================================================
# DOMANDA ENERGETICA (da analisi_meteo.py)
# ============================================================

@domanda_bp.route("/differenza-domanda-zona")
def differenza_domanda_zona():

    try:

        anno = request.args.get("anno")
        zona = request.args.get("zona")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                d.data,
                AVG(d.domanda_effettiva - d.domanda_prevista)
                    AS differenza
            FROM domande d
            JOIN bidding_zones bz
                ON d.zona_id = bz.id
            WHERE d.data >= %s
              AND d.data < %s
              AND bz.nome = %s
            GROUP BY d.data
            ORDER BY d.data
        """

        return jsonify(
            execute_query(
                query,
                [data_inizio, data_fine, zona]
            )
        )

    except Exception as e:
        return handle_error(e)


@domanda_bp.route("/domanda-media-mensile-nazionale")
def domanda_media_mensile_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(data) AS mese,
                AVG(domanda_effettiva) AS domanda_media
            FROM domande
            WHERE data >= %s
              AND data < %s
            GROUP BY MONTH(data)
            ORDER BY mese
        """

        return jsonify(
            execute_query(
                query,
                [data_inizio, data_fine]
            )
        )

    except Exception as e:
        return handle_error(e)


@domanda_bp.route("/domanda-media-mensile-zona")
def domanda_media_mensile_zona():

    try:

        anno = request.args.get("anno")
        zona = request.args.get("zona")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(d.data) AS mese,
                AVG(d.domanda_effettiva) AS domanda_media
            FROM domande d
            JOIN bidding_zones bz
                ON d.zona_id = bz.id
            WHERE d.data >= %s
              AND d.data < %s
              AND bz.nome = %s
            GROUP BY MONTH(d.data)
            ORDER BY mese
        """

        return jsonify(
            execute_query(
                query,
                [data_inizio, data_fine, zona]
            )
        )

    except Exception as e:
        return handle_error(e)


@domanda_bp.route("/differenza-domanda-effettiva-prevista-nazionale")
def differenza_domanda_effettiva_prevista_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                data,
                AVG(domanda_effettiva - domanda_prevista)
                    AS differenza
            FROM domande
            WHERE data >= %s
              AND data < %s
            GROUP BY data
            ORDER BY data
        """

        return jsonify(
            execute_query(
                query,
                [data_inizio, data_fine]
            )
        )

    except Exception as e:
        return handle_error(e)


# ============================================================
# DOMANDA ENERGETICA (da funzioni_energia.py)
# ============================================================

@domanda_bp.route("/domanda-media")
def domanda_media():

    query = """
        SELECT
            b.nome AS bidding_zone,
            AVG(d.domanda_effettiva) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY b.nome
        ORDER BY domanda_media DESC
    """

    return jsonify(execute_query(query))


@domanda_bp.route("/domanda-media-mensile")
def domanda_media_mensile():

    query = """
        SELECT
            bidding_zone,
            mese,
            AVG(domanda_media_giornaliera) AS domanda_media_mensile
        FROM (
            SELECT
                b.nome AS bidding_zone,
                d.data,
                MONTH(d.data) AS mese,
                AVG(d.domanda_effettiva) AS domanda_media_giornaliera
            FROM domande AS d
            JOIN bidding_zones AS b
                ON d.zona_id = b.id
            WHERE YEAR(d.data) = 2025
            GROUP BY b.nome, d.data
        ) AS medie_giornaliere
        GROUP BY bidding_zone, mese
        ORDER BY bidding_zone, mese
    """

    return jsonify(execute_query(query))


@domanda_bp.route("/domanda-max-min-giornaliera")
def domanda_max_min_giornaliera():

    query = """
        SELECT
            b.nome AS bidding_zone,
            d.data,
            AVG(d.domanda_effettiva) AS domanda_media_giornaliera
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            d.data
        ORDER BY
            b.nome,
            d.data
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]

        if zona not in risultato:
            risultato[zona] = {
                "giorno_max": None,
                "domanda_media_max": None,
                "giorno_min": None,
                "domanda_media_min": None
            }

        media = riga["domanda_media_giornaliera"]

        if (
            risultato[zona]["domanda_media_max"] is None
            or media > risultato[zona]["domanda_media_max"]
        ):
            risultato[zona]["giorno_max"] = riga["data"]
            risultato[zona]["domanda_media_max"] = media

        if (
            risultato[zona]["domanda_media_min"] is None
            or media < risultato[zona]["domanda_media_min"]
        ):
            risultato[zona]["giorno_min"] = riga["data"]
            risultato[zona]["domanda_media_min"] = media

    return jsonify(risultato)


@domanda_bp.route("/mese-media-domanda-max-min")
def mese_media_domanda_max_min():

    query = """
        SELECT
            b.nome AS bidding_zone,
            MONTH(d.data) AS mese,
            AVG(d.domanda_effettiva) AS domanda_media_mensile
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            MONTH(d.data)
        ORDER BY
            b.nome,
            mese
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]
        media = riga["domanda_media_mensile"]

        if zona not in risultato:
            risultato[zona] = {
                "mese_max": None,
                "domanda_media_max": None,
                "mese_min": None,
                "domanda_media_min": None
            }

        if (
            risultato[zona]["domanda_media_max"] is None
            or media > risultato[zona]["domanda_media_max"]
        ):
            risultato[zona]["mese_max"] = riga["mese"]
            risultato[zona]["domanda_media_max"] = media

        if (
            risultato[zona]["domanda_media_min"] is None
            or media < risultato[zona]["domanda_media_min"]
        ):
            risultato[zona]["mese_min"] = riga["mese"]
            risultato[zona]["domanda_media_min"] = media

    return jsonify(risultato)


@domanda_bp.route("/ranking-orario-domanda")
def ranking_orario_domanda():

    query = """
        SELECT
            b.nome AS bidding_zone,
            HOUR(d.orario) AS ora,
            AVG(d.domanda_effettiva) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            HOUR(d.orario)
        ORDER BY
            b.nome,
            domanda_media DESC
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]

        if zona not in risultato:
            risultato[zona] = []

        risultato[zona].append({
            "ora": riga["ora"],
            "domanda_media": riga["domanda_media"]
        })

    for zona in risultato:

        for posizione, riga in enumerate(risultato[zona], start=1):
            riga["ranking"] = posizione

        risultato[zona] = [
            {
                "ranking": riga["ranking"],
                "ora": riga["ora"],
                "domanda_media": riga["domanda_media"]
            }
            for riga in risultato[zona]
        ]

    return jsonify(risultato)


@domanda_bp.route("/domanda-media-oraria")
def domanda_media_oraria():

    query = """
        SELECT
            b.nome AS bidding_zone,
            HOUR(d.orario) AS ora,
            ROUND(AVG(d.domanda_effettiva), 2) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            HOUR(d.orario)
        ORDER BY
            b.nome,
            ora
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]

        if zona not in risultato:
            risultato[zona] = []

        risultato[zona].append({
            "ora": riga["ora"],
            "domanda_media": riga["domanda_media"]
        })

    return jsonify(risultato)


@domanda_bp.route("/domanda-media-giorno-settimana")
def domanda_media_giorno_settimana():

    query = """
        SELECT
            b.nome AS bidding_zone,
            WEEKDAY(d.data) AS numero_giorno,
            DAYNAME(d.data) AS giorno_settimana,
            ROUND(AVG(d.domanda_effettiva), 2) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            WEEKDAY(d.data),
            DAYNAME(d.data)
        ORDER BY
            b.nome,
            numero_giorno
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]

        if zona not in risultato:
            risultato[zona] = []

        risultato[zona].append({
            "giorno_settimana": riga["giorno_settimana"],
            "domanda_media": riga["domanda_media"]
        })

    return jsonify(risultato)


@domanda_bp.route("/giorno-picco-assoluto")
def giorno_picco_assoluto():

    query = """
        SELECT
            b.nome AS bidding_zone,
            d.data,
            ROUND(AVG(d.domanda_effettiva), 2) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            d.data
        ORDER BY
            b.nome,
            domanda_media DESC
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]

        if zona not in risultato:
            risultato[zona] = {
                "data": riga["data"],
                "domanda_media": riga["domanda_media"]
            }

    return jsonify(risultato)


@domanda_bp.route("/bidding-zone-maggiore-variabilita")
def bidding_zone_maggiore_variabilita():

    query = """
        SELECT
            b.nome AS bidding_zone,
            d.data,
            AVG(d.domanda_effettiva) AS domanda_media
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            d.data
        ORDER BY
            b.nome,
            d.data
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]
        media = float(riga["domanda_media"])

        if zona not in risultato:
            risultato[zona] = {
                "giorno_picco": riga["data"],
                "domanda_media_picco": media,
                "giorno_minimo": riga["data"],
                "domanda_media_minimo": media
            }

        if media > risultato[zona]["domanda_media_picco"]:
            risultato[zona]["giorno_picco"] = riga["data"]
            risultato[zona]["domanda_media_picco"] = media

        if media < risultato[zona]["domanda_media_minimo"]:
            risultato[zona]["giorno_minimo"] = riga["data"]
            risultato[zona]["domanda_media_minimo"] = media

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di domanda per il 2025."
        })

    for zona in risultato:

        picco = risultato[zona]["domanda_media_picco"]
        minimo = risultato[zona]["domanda_media_minimo"]

        variabilita = ((picco - minimo) / minimo) * 100

        risultato[zona]["variabilita_percentuale"] = round(variabilita, 2)

    zona_maggiore = max(
        risultato,
        key=lambda zona: risultato[zona]["variabilita_percentuale"]
    )

    return jsonify({
        "bidding_zone": zona_maggiore,
        **risultato[zona_maggiore]
    })


@domanda_bp.route("/deviazione-standard-giornaliera")
def deviazione_standard_giornaliera():

    query = """
        SELECT
            b.nome AS bidding_zone,
            d.data,
            AVG(d.domanda_effettiva) AS domanda_media_giornaliera
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
        GROUP BY
            b.nome,
            d.data
        ORDER BY
            b.nome,
            d.data
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]
        media = float(riga["domanda_media_giornaliera"])

        if zona not in risultato:
            risultato[zona] = []

        risultato[zona].append(media)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di domanda per il 2025."
        })

    output = {}

    for zona, medie in risultato.items():

        media_annuale = statistics.mean(medie)
        deviazione = statistics.pstdev(medie)
        coefficiente_variazione = (deviazione / media_annuale) * 100

        output[zona] = {
            "media_annuale": round(media_annuale, 2),
            "deviazione_standard": round(deviazione, 2),
            "deviazione_percentuale": round(coefficiente_variazione, 2),
            "numero_giorni": len(medie)
        }

    return jsonify(output)


@domanda_bp.route("/differenza-prevista-effettiva")
def differenza_prevista_effettiva():

    query = """
        SELECT
            b.nome AS bidding_zone,
            d.data,
            AVG(d.domanda_effettiva) AS media_effettiva,
            AVG(d.domanda_prevista) AS media_prevista
        FROM domande AS d
        JOIN bidding_zones AS b
            ON d.zona_id = b.id
        WHERE YEAR(d.data) = 2025
          AND d.domanda_effettiva IS NOT NULL
          AND d.domanda_prevista IS NOT NULL
        GROUP BY
            b.nome,
            d.data
        ORDER BY
            b.nome,
            d.data
    """

    dati = execute_query(query)

    risultato = {}

    for riga in dati:

        zona = riga["bidding_zone"]
        media_effettiva = float(riga["media_effettiva"])
        media_prevista = float(riga["media_prevista"])

        if media_prevista == 0:
            continue

        differenza_percentuale = (
            abs(media_effettiva - media_prevista) / media_prevista
        ) * 100

        if zona not in risultato:
            risultato[zona] = {
                "giorno_differenza_minima": riga["data"],
                "differenza_minima_percentuale": differenza_percentuale,
                "giorno_differenza_massima": riga["data"],
                "differenza_massima_percentuale": differenza_percentuale
            }

        if (
            differenza_percentuale
            < risultato[zona]["differenza_minima_percentuale"]
        ):
            risultato[zona]["giorno_differenza_minima"] = riga["data"]
            risultato[zona]["differenza_minima_percentuale"] = differenza_percentuale

        if (
            differenza_percentuale
            > risultato[zona]["differenza_massima_percentuale"]
        ):
            risultato[zona]["giorno_differenza_massima"] = riga["data"]
            risultato[zona]["differenza_massima_percentuale"] = differenza_percentuale

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati validi per il 2025."
        })

    for zona in risultato:

        risultato[zona]["differenza_minima_percentuale"] = round(
            risultato[zona]["differenza_minima_percentuale"], 2
        )

        risultato[zona]["differenza_massima_percentuale"] = round(
            risultato[zona]["differenza_massima_percentuale"], 2
        )

    return jsonify(risultato)
