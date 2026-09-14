from flask import Blueprint, jsonify, request

from ..db import execute_query, execute_single_query
from ..utils import handle_error

capacita_bp = Blueprint("capacita", __name__)


# ============================================================
# CAPACITÀ INSTALLATA (da analisi_meteo.py / analisi_energia.py)
# ============================================================

@capacita_bp.route("/capacita-media-impianto")
def capacita_media_impianto():
    """Media semplice della potenza nominale, con filtri opzionali."""

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")
        fonte = request.args.get("fonte")

        query = """
            SELECT
                AVG(c.potenza_nominale) AS potenza_media
            FROM capacita_installate c
            JOIN province p
                ON c.provincia_id = p.id
            JOIN fonti_energetiche f
                ON c.fonte_id = f.id
            WHERE 1 = 1
        """

        params = []

        if anno:
            query += " AND c.anno = %s"
            params.append(anno)

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        if fonte:
            query += " AND f.nome = %s"
            params.append(fonte)

        return jsonify(
            execute_single_query(query, params)
        )

    except Exception as e:
        return handle_error(e)


@capacita_bp.route("/capacita-media-impianto-per-fonte")
def capacita_media_impianto_per_fonte():
    """
    Breakdown per anno/mese/fonte: potenza nominale totale,
    numero impianti totale e capacità media per impianto.
    """

    anno = request.args.get("anno")
    fonte = request.args.get("fonte")

    try:
        anno_int = int(anno) if anno else None

        if anno_int is not None:
            if anno_int < 1900 or anno_int > 2100:
                raise ValueError

    except ValueError:
        return jsonify({
            "errore": "Formato anno non valido. Usa YYYY."
        }), 400

    query = """
        SELECT
            c.anno,
            c.mese,
            f.id AS fonte_id,
            f.nome AS fonte,

            SUM(c.potenza_nominale)
                AS potenza_nominale_totale,

            SUM(c.numero_impianti)
                AS numero_impianti_totale,

            SUM(c.potenza_nominale)
            /
            NULLIF(
                SUM(c.numero_impianti),
                0
            ) AS capacita_media_impianto

        FROM capacita_installate c

        INNER JOIN fonti_energetiche f
            ON c.fonte_id = f.id

        WHERE 1 = 1
    """

    parametri = []

    if anno_int is not None:
        query += " AND c.anno = %s"
        parametri.append(anno_int)

    if fonte:
        query += " AND f.nome = %s"
        parametri.append(fonte)

    query += """
        GROUP BY
            c.anno,
            c.mese,
            f.id,
            f.nome

        ORDER BY
            c.anno,
            c.mese,
            f.nome
    """

    try:
        risultati = execute_query(query, parametri)

        dati = []

        for riga in risultati:

            dati.append({
                "anno": int(riga["anno"]),
                "mese": int(riga["mese"]),
                "fonte_id": int(riga["fonte_id"]),
                "fonte": riga["fonte"],

                "potenza_nominale_totale":
                    float(riga["potenza_nominale_totale"]),

                "numero_impianti_totale":
                    int(riga["numero_impianti_totale"]),

                "capacita_media_impianto":
                    float(riga["capacita_media_impianto"])
                    if riga["capacita_media_impianto"] is not None
                    else None
            })

        return jsonify({
            "anno": anno_int,
            "fonte": fonte,

            "domanda_analisi":
                "Qual è la capacità media "
                "di un impianto per fonte energetica?",

            "formula":
                "potenza nominale totale / "
                "numero totale di impianti",

            "unita_capacita":
                "stessa unità di misura della "
                "potenza nominale",

            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


# ============================================================
# CAPACITÀ INSTALLATA (da funzioni_energia.py)
# ============================================================

@capacita_bp.route("/capacita-totale-provincia")
def capacita_totale_provincia():

    query = """
        SELECT
            p.nome AS provincia,
            ROUND(SUM(c.potenza_nominale), 2) AS capacita_totale
        FROM capacita_installate AS c
        JOIN province AS p
            ON c.provincia_id = p.id
        WHERE c.anno = 2025
        GROUP BY
            p.id,
            p.nome
        ORDER BY
            capacita_totale DESC
    """

    risultato = execute_query(query)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di capacità installata per il 2025."
        })

    return jsonify(risultato)


@capacita_bp.route("/capacita-totale-fonte")
def capacita_totale_fonte():

    query = """
        SELECT
            f.nome AS fonte,
            ROUND(SUM(c.potenza_nominale), 2) AS capacita_totale
        FROM capacita_installate AS c
        JOIN fonti_energetiche AS f
            ON c.fonte_id = f.id
        WHERE c.anno = 2025
        GROUP BY
            f.id,
            f.nome
        ORDER BY
            capacita_totale DESC
    """

    risultato = execute_query(query)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di capacità installata per il 2025."
        })

    return jsonify(risultato)


@capacita_bp.route("/capacita-totale-regione")
def capacita_totale_regione():

    query = """
        SELECT
            r.nome AS regione,
            ROUND(SUM(c.potenza_nominale), 2) AS capacita_totale
        FROM capacita_installate AS c
        JOIN province AS p
            ON c.provincia_id = p.id
        JOIN regioni AS r
            ON p.regione_id = r.id
        WHERE c.anno = 2025
        GROUP BY
            r.id,
            r.nome
        ORDER BY
            capacita_totale DESC
    """

    risultato = execute_query(query)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati di capacità installata per il 2025."
        })

    return jsonify(risultato)


@capacita_bp.route("/provincia-maggiore-capacita-fonte")
def provincia_maggiore_capacita_fonte():

    query = """
        SELECT
            f.nome AS fonte,
            p.nome AS provincia,
            ROUND(SUM(c.potenza_nominale), 2) AS capacita_totale
        FROM capacita_installate AS c
        JOIN province AS p
            ON c.provincia_id = p.id
        JOIN fonti_energetiche AS f
            ON c.fonte_id = f.id
        WHERE c.anno = 2025
        GROUP BY
            f.id,
            f.nome,
            p.id,
            p.nome
        ORDER BY
            f.nome,
            capacita_totale DESC
    """

    dati = execute_query(query)

    if not dati:
        return jsonify({
            "errore": "Non sono presenti dati di capacità installata per il 2025."
        })

    risultato = {}

    for riga in dati:

        fonte = riga["fonte"]

        if fonte not in risultato:
            risultato[fonte] = {
                "provincia": riga["provincia"],
                "capacita_totale": riga["capacita_totale"]
            }

    return jsonify(risultato)


@capacita_bp.route("/numero-impianti-provincia")
def numero_impianti_provincia():

    query = """
        SELECT
            p.nome AS provincia,
            SUM(c.numero_impianti) AS numero_impianti
        FROM capacita_installate AS c
        JOIN province AS p
            ON c.provincia_id = p.id
        WHERE c.anno = 2025
        GROUP BY
            p.id,
            p.nome
        ORDER BY
            numero_impianti DESC
    """

    risultato = execute_query(query)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati sugli impianti per il 2025."
        })

    return jsonify(risultato)


@capacita_bp.route("/numero-impianti-classe-potenza")
def numero_impianti_classe_potenza():

    query = """
        SELECT
            c.classe_potenza,
            SUM(c.numero_impianti) AS numero_impianti
        FROM capacita_installate AS c
        WHERE c.anno = 2025
          AND c.classe_potenza IS NOT NULL
        GROUP BY
            c.classe_potenza
        ORDER BY
            numero_impianti DESC
    """

    risultato = execute_query(query)

    if not risultato:
        return jsonify({
            "errore": "Non sono presenti dati sugli impianti per il 2025."
        })

    return jsonify(risultato)
