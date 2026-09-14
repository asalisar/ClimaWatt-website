from flask import Blueprint, jsonify, request

from ..db import execute_query, execute_single_query
from ..utils import get_period_range, get_year_range, handle_error

meteo_bp = Blueprint("meteo", __name__)


# ============================================================
# TEMPERATURA
# ============================================================

@meteo_bp.route("/temperatura-media-giornaliera")
def temperatura_media_giornaliera():

    try:

        anno = request.args.get("anno")
        mese = request.args.get("mese")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_period_range(anno=anno, mese=mese)

        query = """
            SELECT
                m.data,
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
            GROUP BY m.data
            ORDER BY m.data
        """

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/temperatura-massima-giornaliera")
def temperatura_massima_giornaliera():

    try:

        anno = request.args.get("anno")
        mese = request.args.get("mese")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_period_range(anno=anno, mese=mese)

        query = """
            SELECT
                m.data,
                MAX(m.temperatura) AS temperatura_massima
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

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/temperatura-minima-giornaliera")
def temperatura_minima_giornaliera():

    try:

        anno = request.args.get("anno")
        mese = request.args.get("mese")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_period_range(anno=anno, mese=mese)

        query = """
            SELECT
                m.data,
                MIN(m.temperatura) AS temperatura_minima
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

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/temperatura-deviazione-standard-giornaliera")
def temperatura_deviazione_standard_giornaliera():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/temperatura-media-fascia-oraria")
def temperatura_media_fascia_oraria():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/temperatura-media-max-mensile")
def temperatura_media_max_mensile():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(m.data) AS mese,
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
            GROUP BY MONTH(m.data)
            ORDER BY mese
        """

        risultati = execute_query(query, params)

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-caldo-provincia")
def gg_piu_caldo_provincia():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                p.nome AS provincia,
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY p.nome, m.data
            ORDER BY temperatura_media DESC
            LIMIT 1
        """

        risultati = execute_query(
            query,
            [data_inizio, data_fine]
        )

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-caldo-nazionale")
def gg_piu_caldo_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY m.data
            ORDER BY temperatura_media DESC
            LIMIT 1
        """

        risultato = execute_single_query(
            query,
            [data_inizio, data_fine]
        )

        return jsonify(risultato)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-freddo-provincia")
def gg_piu_freddo_provincia():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                p.nome AS provincia,
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY p.nome, m.data
            ORDER BY temperatura_media ASC
            LIMIT 1
        """

        risultati = execute_query(
            query,
            [data_inizio, data_fine]
        )

        return jsonify(risultati)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-freddo-nazionale")
def gg_piu_freddo_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY m.data
            ORDER BY temperatura_media ASC
            LIMIT 1
        """

        risultato = execute_single_query(
            query,
            [data_inizio, data_fine]
        )

        return jsonify(risultato)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/ora-piu-calda-anno-provincia")
def ora_piu_calda_anno_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                HOUR(m.orario) AS ora,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
            GROUP BY HOUR(m.orario)
            ORDER BY temperatura_media DESC
            LIMIT 1
        """

        risultato = execute_single_query(
            query,
            [data_inizio, data_fine, provincia]
        )

        return jsonify(risultato)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/ora-piu-fredda-provincia")
def ora_piu_fredda_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                HOUR(m.orario) AS ora,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
            GROUP BY HOUR(m.orario)
            ORDER BY temperatura_media ASC
            LIMIT 1
        """

        risultato = execute_single_query(
            query,
            [data_inizio, data_fine, provincia]
        )

        return jsonify(risultato)

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/ora-picco-temperatura")
def ora_picco_temperatura():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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
            ORDER BY temperatura_media DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(query, params)
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/escursione-termica-media")
def escursione_termica_media():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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


@meteo_bp.route("/giorni-soglia-temperatura")
def giorni_soglia_temperatura():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")
        soglia = float(request.args.get("soglia"))

        anno, data_inizio, data_fine = get_year_range(anno)

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

        return jsonify(
            execute_single_query(query, params)
        )

    except Exception as e:
        return handle_error(e)


# ============================================================
# VENTO
# ============================================================

@meteo_bp.route("/vento-medio-giornaliero")
def vento_medio_giornaliero():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.vento) AS vento_medio
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


@meteo_bp.route("/vento-medio-giornaliero-regione")
def vento_medio_giornaliero_regione():

    try:

        anno = request.args.get("anno")
        regione = request.args.get("regione")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            JOIN regioni r
                ON p.regione_id = r.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if regione:
            query += " AND r.nome = %s"
            params.append(regione)

        query += """
            GROUP BY m.data
            ORDER BY m.data
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/vento-massimo-giornaliero")
def vento_massimo_giornaliero():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                MAX(m.vento) AS vento_massimo
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


@meteo_bp.route("/vento-minimo-giornaliero")
def vento_minimo_giornaliero():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                MIN(m.vento) AS vento_minimo
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


@meteo_bp.route("/vento-deviazione-standard-giornaliera")
def vento_deviazione_standard_giornaliera():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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


@meteo_bp.route("/vento-medio-fascia-oraria-anno")
def vento_medio_fascia_oraria_anno():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                HOUR(m.orario) AS ora,
                AVG(m.vento) AS vento_medio
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


@meteo_bp.route("/province-vento-medio-annuale")
def province_vento_medio_annuale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                p.nome AS provincia,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY p.nome
            ORDER BY vento_medio DESC
        """

        return jsonify(
            execute_query(query, [data_inizio, data_fine])
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/mese-piu-ventoso-regione")
def mese_piu_ventoso_regione():

    try:

        anno = request.args.get("anno")
        regione = request.args.get("regione")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(m.data) AS mese,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            JOIN regioni r
                ON p.regione_id = r.id
            WHERE m.data >= %s
              AND m.data < %s
        """

        params = [data_inizio, data_fine]

        if regione:
            query += " AND r.nome = %s"
            params.append(regione)

        query += """
            GROUP BY MONTH(m.data)
            ORDER BY vento_medio DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(query, params)
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/vento-media-max-mensile")
def vento_media_max_mensile():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(m.data) AS mese,
                AVG(m.vento) AS vento_medio
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
            GROUP BY MONTH(m.data)
            ORDER BY vento_medio DESC
        """

        return jsonify(execute_query(query, params))

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-ventoso-provincia")
def gg_piu_ventoso_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
            GROUP BY m.data
            ORDER BY vento_medio DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, provincia]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/gg-piu-ventoso-nazionale")
def gg_piu_ventoso_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.data,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY m.data
            ORDER BY vento_medio DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/ora-piu-ventosa-anno-provincia")
def ora_piu_ventosa_anno_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                HOUR(m.orario) AS ora,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
            GROUP BY HOUR(m.orario)
            ORDER BY vento_medio DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, provincia]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/ore-vento-sopra-soglia-provincia")
def ore_vento_sopra_soglia_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")
        soglia = request.args.get("soglia", 10)

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                COUNT(*) AS ore_sopra_soglia
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
              AND m.vento > %s
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, provincia, soglia]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/vento-medio-mensile-nazionale")
def vento_medio_mensile_nazionale():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(data) AS mese,
                AVG(vento) AS vento_medio
            FROM meteo
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


@meteo_bp.route("/vento-medio-mensile-regioni")
def vento_medio_mensile_regioni():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                r.nome AS regione,
                MONTH(m.data) AS mese,
                AVG(m.vento) AS vento_medio
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            JOIN regioni r
                ON p.regione_id = r.id
            WHERE m.data >= %s
              AND m.data < %s
            GROUP BY r.nome, MONTH(m.data)
            ORDER BY r.nome, mese
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
# RADIAZIONE
# ============================================================

@meteo_bp.route("/radiazione-stats-provincia")
def radiazione_stats_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

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
              AND p.nome = %s
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, provincia]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/giorno-picco-radiazione")
def giorno_picco_radiazione():

    try:

        anno = request.args.get("anno")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                data,
                AVG(radiazione) AS radiazione_media
            FROM meteo
            WHERE data >= %s
              AND data < %s
            GROUP BY data
            ORDER BY radiazione_media DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/variabilita-radiazione-zona")
def variabilita_radiazione_zona():

    try:

        anno = request.args.get("anno")
        zona = request.args.get("zona")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                STDDEV(m.radiazione) AS deviazione_standard
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            JOIN regioni r
                ON p.regione_id = r.id
            WHERE m.data >= %s
              AND m.data < %s
              AND r.nome = %s
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, zona]
            )
        )

    except Exception as e:
        return handle_error(e)


@meteo_bp.route("/mese-max-radiazione-provincia")
def mese_max_radiazione_provincia():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                MONTH(m.data) AS mese,
                AVG(m.radiazione) AS radiazione_media
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND p.nome = %s
            GROUP BY MONTH(m.data)
            ORDER BY radiazione_media DESC
            LIMIT 1
        """

        return jsonify(
            execute_single_query(
                query,
                [data_inizio, data_fine, provincia]
            )
        )

    except Exception as e:
        return handle_error(e)
