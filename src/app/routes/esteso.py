"""
Blueprint aggiuntivo: nuove statistiche (radiazione giornaliera) e
versioni delle statistiche esistenti che accettano anche un giorno
specifico (non solo mese o anno), senza toccare meteo.py.

Per attivarlo, in src/app/__init__.py aggiungere:

    from .routes.esteso import esteso_bp
    ...
    app.register_blueprint(esteso_bp)
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from ..db import execute_query, execute_single_query
from ..utils import get_month_range, get_year_range, handle_error

esteso_bp = Blueprint("esteso", __name__)


def get_day_range(giorno):
    """Riceve un giorno YYYY-MM-DD e restituisce (anno, inizio, fine)."""

    try:
        data = datetime.strptime(giorno, "%Y-%m-%d")
        data_fine = data + timedelta(days=1)

        return (
            data.year,
            data.strftime("%Y-%m-%d"),
            data_fine.strftime("%Y-%m-%d")
        )

    except ValueError:
        raise ValueError(
            "Formato giorno non valido. Usa YYYY-MM-DD."
        )


def get_periodo(anno=None, mese=None, giorno=None):
    """
    Restituisce (anno, data_inizio, data_fine) usando 'giorno'
    (YYYY-MM-DD) se presente, altrimenti 'mese' (YYYY-MM),
    altrimenti 'anno' (YYYY).
    """

    if giorno:
        return get_day_range(giorno)

    if mese:
        return get_month_range(mese)

    return get_year_range(anno)


def _parametri_periodo():
    return (
        request.args.get("anno"),
        request.args.get("mese"),
        request.args.get("giorno"),
        request.args.get("provincia"),
    )


# ============================================================
# RADIAZIONE GIORNALIERA (nuovi, non esistevano in meteo.py)
# ============================================================

@esteso_bp.route("/radiazione-media-giornaliera")
def radiazione_media_giornaliera():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                AVG(m.radiazione) AS radiazione_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/radiazione-massima-giornaliera")
def radiazione_massima_giornaliera():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                MAX(m.radiazione) AS radiazione_massima
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/radiazione-cumulata-giornaliera")
def radiazione_cumulata_giornaliera():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                SUM(m.radiazione) AS radiazione_cumulata
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


# ============================================================
# VERSIONI "PERIODO" (anno / mese / giorno) DI STATISTICHE
# GIA' ESISTENTI IN meteo.py, ma li' solo con anno (o anno+mese)
# ============================================================

@esteso_bp.route("/temperatura-deviazione-standard-periodo")
def temperatura_deviazione_standard_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                STDDEV(m.temperatura) AS deviazione_standard
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/temperatura-fascia-oraria-periodo")
def temperatura_fascia_oraria_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                HOUR(m.orario) AS ora,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY HOUR(m.orario)
            ORDER BY ora
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/escursione-termica-periodo")
def escursione_termica_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                MAX(m.temperatura) - MIN(m.temperatura)
                    AS escursione_termica
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/giorni-soglia-temperatura-periodo")
def giorni_soglia_temperatura_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        soglia = float(request.args.get("soglia"))

        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                COUNT(DISTINCT m.data) AS giorni
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND m.temperatura > %s
        """

        params = [data_inizio, data_fine, soglia]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        return jsonify(execute_single_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/giorni-soglia-vento-periodo")
def giorni_soglia_vento_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        soglia = float(request.args.get("soglia"))

        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                COUNT(DISTINCT m.data) AS giorni
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND m.vento > %s
        """

        params = [data_inizio, data_fine, soglia]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        return jsonify(execute_single_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/vento-deviazione-standard-periodo")
def vento_deviazione_standard_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                m.data,
                STDDEV(m.vento) AS deviazione_standard
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/radiazione-stats-periodo")
def radiazione_stats_periodo():

    try:
        anno, mese, giorno, provincia = _parametri_periodo()
        anno, data_inizio, data_fine = get_periodo(anno, mese, giorno)

        query = """
            SELECT
                AVG(m.radiazione) AS media,
                MAX(m.radiazione) AS massimo,
                MIN(m.radiazione) AS minimo,
                STDDEV(m.radiazione) AS deviazione_standard
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        return jsonify(execute_single_query(query, params))

    except Exception as e:
        return handle_error(e)


# ============================================================
# MOMENTO ESATTO (giorno + ora) PIU' CALDO/FREDDO DELL'ANNO
# ============================================================

@esteso_bp.route("/momento-piu-caldo-anno-provincia")
def momento_piu_caldo_anno_provincia():

    anno = request.args.get("anno", default="2025")
    provincia = request.args.get("provincia")

    try:
        anno_int = int(anno)
    except (TypeError, ValueError):
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        SELECT
            m.data,
            HOUR(m.orario) AS ora,
            m.temperatura
        FROM meteo m
        JOIN province p
            ON m.provincia_id = p.id
        WHERE YEAR(m.data) = %s
          AND m.temperatura IS NOT NULL
    """

    params = [anno_int]

    if provincia:
        query += " AND p.nome = %s"
        params.append(provincia)

    query += " ORDER BY m.temperatura DESC LIMIT 1"

    try:
        return jsonify(execute_single_query(query, params))
    except Exception as e:
        return handle_error(e)


@esteso_bp.route("/momento-piu-freddo-anno-provincia")
def momento_piu_freddo_anno_provincia():

    anno = request.args.get("anno", default="2025")
    provincia = request.args.get("provincia")

    try:
        anno_int = int(anno)
    except (TypeError, ValueError):
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        SELECT
            m.data,
            HOUR(m.orario) AS ora,
            m.temperatura
        FROM meteo m
        JOIN province p
            ON m.provincia_id = p.id
        WHERE YEAR(m.data) = %s
          AND m.temperatura IS NOT NULL
    """

    params = [anno_int]

    if provincia:
        query += " AND p.nome = %s"
        params.append(provincia)

    query += " ORDER BY m.temperatura ASC LIMIT 1"

    try:
        return jsonify(execute_single_query(query, params))
    except Exception as e:
        return handle_error(e)
