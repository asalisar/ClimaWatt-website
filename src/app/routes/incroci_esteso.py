"""
Nuove analisi incrociate meteo/energia, tratte da
analisi_meteo_energia.py (versione aggiornata). Non tocca incroci.py:
gli endpoint gia' presenti li' (identici o equivalenti nella versione
aggiornata) non vengono ripetuti qui:

    /temperatura-errore-previsione-domanda
    /indice-solare-produzione-fotovoltaica
    /domanda-per-fasce-temperatura
    /correlazione-temperatura-domanda

Nota sul nome: la versione aggiornata di /vento-produzione-eolica usa
una logica diversa (vento pesato per capacita' eolica installata,
aggregato a livello nazionale) rispetto a quella gia' in incroci.py
(media vento semplice per zona). Per non avere due endpoint con lo
stesso nome e comportamento diverso, questa versione e' esposta come
/vento-produzione-eolica-pesato.

Per attivare, in src/app/__init__.py aggiungere:

    from .routes.incroci_esteso import incroci_esteso_bp
    ...
    app.register_blueprint(incroci_esteso_bp)
"""

import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from scipy.stats import kruskal

from ..db import execute_query
from ..utils import handle_error

incroci_esteso_bp = Blueprint("incroci_esteso", __name__)


def _anno_valido(anno_str):

    try:
        anno_int = int(anno_str)

        if anno_int < 1900 or anno_int > 2100:
            raise ValueError

        return anno_int

    except (TypeError, ValueError):
        return None


# ============================================================
# GRAFICO ERRORE PREVISIONE IN BASE A TEMPERATURA
# ============================================================

@incroci_esteso_bp.route("/grafico-temperatura-errore-previsione-domanda")
def grafico_temperatura_errore_previsione_domanda():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))
    zona = request.args.get("zona")

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH temperatura_giornaliera AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            INNER JOIN province p ON m.provincia_id = p.id
            INNER JOIN regioni r ON p.regione_id = r.id
            INNER JOIN bidding_zones z ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s
            GROUP BY z.id, z.nome, m.data
        ),
        temperatura_classificata AS (
            SELECT
                zona_id, zona, data, temperatura_media,
                NTILE(10) OVER (
                    PARTITION BY zona_id ORDER BY temperatura_media
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
            INNER JOIN bidding_zones z ON d.zona_id = z.id
            WHERE YEAR(d.data) = %s
            GROUP BY z.id, z.nome, d.data
        ),
        dati_completi AS (
            SELECT
                t.zona_id, t.zona, t.data,
                t.temperatura_media, t.decile_temperatura,
                d.domanda_effettiva, d.domanda_prevista, d.errore_assoluto,
                CASE
                    WHEN t.decile_temperatura IN (1, 2) THEN 'freddo_estremo'
                    WHEN t.decile_temperatura IN (9, 10) THEN 'caldo_estremo'
                    ELSE 'normale'
                END AS tipo_periodo
            FROM temperatura_classificata t
            INNER JOIN domanda_giornaliera d
                ON t.zona_id = d.zona_id AND t.data = d.data
        )
        SELECT
            zona,
            tipo_periodo,
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

    query += " GROUP BY zona, tipo_periodo"

    try:
        risultati = execute_query(query, parametri)

        df = pd.DataFrame(risultati)

        if df.empty:
            return jsonify({"errore": "Nessun dato disponibile."}), 404

        df["errore_percentuale_medio"] = df["errore_percentuale_medio"].astype(float)

        ordine_periodi = ["freddo_estremo", "normale", "caldo_estremo"]

        df["tipo_periodo"] = pd.Categorical(
            df["tipo_periodo"], categories=ordine_periodi, ordered=True
        )

        df = df.sort_values(["zona", "tipo_periodo"])

        plt.figure(figsize=(12, 7))

        for nome_zona in df["zona"].unique():

            dati_zona = df[df["zona"] == nome_zona]

            plt.plot(
                dati_zona["tipo_periodo"],
                dati_zona["errore_percentuale_medio"],
                marker="o",
                linewidth=2,
                label=nome_zona
            )

        plt.title(
            f"Errore di previsione della domanda nei periodi termici - {anno_int}"
        )
        plt.xlabel("Tipo di periodo")
        plt.ylabel("Errore percentuale medio (%)")
        plt.grid(axis="y", alpha=0.3)
        plt.legend(title="Zona")
        plt.tight_layout()

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)


# ============================================================
# VENTO - PRODUZIONE EOLICA (pesata per capacita' installata)
# ============================================================

_QUERY_VENTO_PESATO_CTE = """
    WITH capacita_eolica_provincia AS (
        SELECT
            c.anno, c.mese, c.provincia_id,
            SUM(c.potenza_nominale) AS capacita_eolica
        FROM capacita_installate c
        INNER JOIN fonti_energetiche f ON c.fonte_id = f.id
        WHERE c.anno = %s AND f.nome = 'Wind'
        GROUP BY c.anno, c.mese, c.provincia_id
    ),
    vento_orario_pesato AS (
        SELECT
            m.data, m.orario,
            SUM(m.vento * c.capacita_eolica)
                / NULLIF(SUM(c.capacita_eolica), 0) AS vento_medio_pesato
        FROM meteo m
        INNER JOIN capacita_eolica_provincia c
            ON m.provincia_id = c.provincia_id
           AND YEAR(m.data) = c.anno
           AND MONTH(m.data) = c.mese
        WHERE YEAR(m.data) = %s AND m.vento IS NOT NULL
        GROUP BY m.data, m.orario
    ),
    produzione_eolica AS (
        SELECT
            p.data, p.orario,
            SUM(p.generazione) AS produzione_eolica
        FROM produzioni p
        INNER JOIN fonti_energetiche f ON p.fonte_id = f.id
        WHERE YEAR(p.data) = %s AND f.nome = 'Wind'
        GROUP BY p.data, p.orario
    )
"""


@incroci_esteso_bp.route("/vento-produzione-eolica-pesato")
def vento_produzione_eolica_pesato():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = _QUERY_VENTO_PESATO_CTE + """
        , dati_completi AS (
            SELECT
                v.data, v.orario, v.vento_medio_pesato, e.produzione_eolica,
                CASE
                    WHEN v.vento_medio_pesato < 2 THEN 'vento_molto_debole'
                    WHEN v.vento_medio_pesato < 4 THEN 'vento_debole'
                    WHEN v.vento_medio_pesato < 6 THEN 'vento_moderato'
                    WHEN v.vento_medio_pesato < 8 THEN 'vento_forte'
                    ELSE 'vento_molto_forte'
                END AS fascia_vento
            FROM vento_orario_pesato v
            INNER JOIN produzione_eolica e
                ON v.data = e.data AND v.orario = e.orario
        )
        SELECT
            fascia_vento,
            COUNT(*) AS numero_osservazioni,
            ROUND(AVG(vento_medio_pesato), 2) AS vento_medio_pesato,
            ROUND(MIN(vento_medio_pesato), 2) AS vento_minimo,
            ROUND(MAX(vento_medio_pesato), 2) AS vento_massimo,
            ROUND(AVG(produzione_eolica), 2) AS produzione_eolica_media,
            ROUND(MAX(produzione_eolica), 2) AS produzione_eolica_massima,
            ROUND(STDDEV(produzione_eolica), 2)
                AS deviazione_standard_produzione
        FROM dati_completi
        GROUP BY fascia_vento
        ORDER BY
            CASE fascia_vento
                WHEN 'vento_molto_debole' THEN 1
                WHEN 'vento_debole' THEN 2
                WHEN 'vento_moderato' THEN 3
                WHEN 'vento_forte' THEN 4
                WHEN 'vento_molto_forte' THEN 5
            END
    """

    parametri = [anno_int, anno_int, anno_int]

    try:
        risultati = execute_query(query, parametri)

        dati = [
            {
                "fascia_vento": r["fascia_vento"],
                "numero_osservazioni": int(r["numero_osservazioni"]),
                "vento_medio_pesato": float(r["vento_medio_pesato"]),
                "vento_minimo": float(r["vento_minimo"]),
                "vento_massimo": float(r["vento_massimo"]),
                "produzione_eolica_media": float(r["produzione_eolica_media"]),
                "produzione_eolica_massima": float(r["produzione_eolica_massima"]),
                "deviazione_standard_produzione":
                    float(r["deviazione_standard_produzione"])
            }
            for r in risultati
        ]

        return jsonify({
            "anno": anno_int,
            "domanda_analisi":
                "Come varia la produzione eolica nazionale al variare "
                "del vento nelle aree italiane con capacità eolica "
                "installata?",
            "criterio_analisi":
                "La velocità del vento provinciale viene pesata in base "
                "alla capacità eolica installata nella stessa provincia "
                "e nello stesso mese.",
            "formula_vento_pesato":
                "SUM(vento_provincia * capacità_eolica_provincia) "
                "/ SUM(capacità_eolica_provincia)",
            "numero_risultati": len(dati),
            "dati": dati
        })

    except Exception as e:
        return handle_error(e)


def _grafico_scatter_generico(
    query,
    parametri,
    colonna_x,
    colonna_y,
    titolo,
    xlabel,
    ylabel
):
    """Helper comune per gli scatter con regressione lineare."""

    risultati = execute_query(query, parametri)

    df = pd.DataFrame(risultati)

    if df.empty:
        return jsonify({"errore": "Nessun dato disponibile."}), 404

    df[colonna_x] = df[colonna_x].astype(float)
    df[colonna_y] = df[colonna_y].astype(float)

    pearson = df[colonna_x].corr(df[colonna_y], method="pearson")
    spearman = df[colonna_x].corr(df[colonna_y], method="spearman")

    max_punti = 20000

    df_grafico = (
        df.sample(n=max_punti, random_state=42)
        if len(df) > max_punti
        else df.copy()
    )

    x = df_grafico[colonna_x].to_numpy(dtype=float)
    y = df_grafico[colonna_y].to_numpy(dtype=float)

    coeff = np.polyfit(x, y, 1)
    retta = np.poly1d(coeff)
    x_linea = np.linspace(x.min(), x.max(), 100)

    plt.figure(figsize=(11, 7))
    plt.scatter(x, y, alpha=0.18, s=14)
    plt.plot(x_linea, retta(x_linea), linewidth=2)
    plt.title(f"{titolo}\nPearson = {pearson:.3f} | Spearman = {spearman:.3f}")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(alpha=0.25)
    plt.tight_layout()

    output = io.BytesIO()
    plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    output.seek(0)

    return send_file(output, mimetype="image/png")


@incroci_esteso_bp.route("/scatter-vento-produzione-eolica")
def scatter_vento_produzione_eolica():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = _QUERY_VENTO_PESATO_CTE + """
        SELECT
            v.data, v.orario, v.vento_medio_pesato, e.produzione_eolica
        FROM vento_orario_pesato v
        INNER JOIN produzione_eolica e
            ON v.data = e.data AND v.orario = e.orario
        WHERE v.vento_medio_pesato IS NOT NULL
          AND e.produzione_eolica IS NOT NULL
        ORDER BY v.data, v.orario
    """

    try:
        return _grafico_scatter_generico(
            query,
            [anno_int, anno_int, anno_int],
            "vento_medio_pesato",
            "produzione_eolica",
            f"Vento pesato vs produzione eolica - {anno_int}",
            "Vento medio nazionale pesato per capacità eolica (m/s)",
            "Produzione eolica nazionale"
        )
    except Exception as e:
        return handle_error(e)


@incroci_esteso_bp.route("/scatter-vento-produzione-eolica-non-pesato")
def scatter_vento_produzione_eolica_non_pesato():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH vento_orario AS (
            SELECT
                m.data, m.orario,
                AVG(m.vento) AS vento_medio_nazionale
            FROM meteo m
            WHERE YEAR(m.data) = %s AND m.vento IS NOT NULL
            GROUP BY m.data, m.orario
        ),
        produzione_eolica AS (
            SELECT
                p.data, p.orario,
                SUM(p.generazione) AS produzione_eolica
            FROM produzioni p
            INNER JOIN fonti_energetiche f ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s AND f.nome = 'Wind'
            GROUP BY p.data, p.orario
        )
        SELECT
            v.data, v.orario, v.vento_medio_nazionale, e.produzione_eolica
        FROM vento_orario v
        INNER JOIN produzione_eolica e
            ON v.data = e.data AND v.orario = e.orario
        WHERE v.vento_medio_nazionale IS NOT NULL
          AND e.produzione_eolica IS NOT NULL
        ORDER BY v.data, v.orario
    """

    try:
        return _grafico_scatter_generico(
            query,
            [anno_int, anno_int],
            "vento_medio_nazionale",
            "produzione_eolica",
            f"Vento medio nazionale vs produzione eolica - {anno_int}",
            "Vento medio nazionale non pesato (m/s)",
            "Produzione eolica nazionale"
        )
    except Exception as e:
        return handle_error(e)


@incroci_esteso_bp.route("/scatter-indice-vento-cubo-non-pesato")
def scatter_indice_vento_cubo_non_pesato():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH indice_vento_orario AS (
            SELECT
                m.data, m.orario,
                AVG(POWER(m.vento, 3)) AS indice_vento_cubo
            FROM meteo m
            WHERE YEAR(m.data) = %s AND m.vento IS NOT NULL
            GROUP BY m.data, m.orario
        ),
        produzione_eolica AS (
            SELECT
                p.data, p.orario,
                SUM(p.generazione) AS produzione_eolica
            FROM produzioni p
            INNER JOIN fonti_energetiche f ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s AND f.nome = 'Wind'
            GROUP BY p.data, p.orario
        )
        SELECT
            i.data, i.orario, i.indice_vento_cubo, e.produzione_eolica
        FROM indice_vento_orario i
        INNER JOIN produzione_eolica e
            ON i.data = e.data AND i.orario = e.orario
        WHERE i.indice_vento_cubo IS NOT NULL
          AND e.produzione_eolica IS NOT NULL
        ORDER BY i.data, i.orario
    """

    try:
        return _grafico_scatter_generico(
            query,
            [anno_int, anno_int],
            "indice_vento_cubo",
            "produzione_eolica",
            f"Indice vento³ medio nazionale vs produzione eolica - {anno_int}",
            "Indice climatico medio nazionale AVG(vento³)",
            "Produzione eolica nazionale"
        )
    except Exception as e:
        return handle_error(e)


@incroci_esteso_bp.route("/scatter-indice-climatico-eolico")
def scatter_indice_climatico_eolico():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH capacita_eolica_provincia AS (
            SELECT
                c.anno, c.mese, c.provincia_id,
                SUM(c.potenza_nominale) AS capacita_eolica
            FROM capacita_installate c
            INNER JOIN fonti_energetiche f ON c.fonte_id = f.id
            WHERE c.anno = %s AND f.nome = 'Wind'
            GROUP BY c.anno, c.mese, c.provincia_id
        ),
        indice_climatico_orario AS (
            SELECT
                m.data, m.orario,
                SUM(c.capacita_eolica * POWER(m.vento, 3))
                    / NULLIF(SUM(c.capacita_eolica), 0)
                    AS indice_climatico_eolico
            FROM meteo m
            INNER JOIN capacita_eolica_provincia c
                ON m.provincia_id = c.provincia_id
               AND YEAR(m.data) = c.anno
               AND MONTH(m.data) = c.mese
            WHERE YEAR(m.data) = %s AND m.vento IS NOT NULL
            GROUP BY m.data, m.orario
        ),
        produzione_eolica AS (
            SELECT
                p.data, p.orario,
                SUM(p.generazione) AS produzione_eolica
            FROM produzioni p
            INNER JOIN fonti_energetiche f ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s AND f.nome = 'Wind'
            GROUP BY p.data, p.orario
        )
        SELECT
            i.data, i.orario, i.indice_climatico_eolico, e.produzione_eolica
        FROM indice_climatico_orario i
        INNER JOIN produzione_eolica e
            ON i.data = e.data AND i.orario = e.orario
        WHERE i.indice_climatico_eolico IS NOT NULL
          AND e.produzione_eolica IS NOT NULL
        ORDER BY i.data, i.orario
    """

    try:
        return _grafico_scatter_generico(
            query,
            [anno_int, anno_int, anno_int],
            "indice_climatico_eolico",
            "produzione_eolica",
            f"Indice climatico eolico vs produzione - {anno_int}",
            "Indice climatico eolico Σ(capacità × vento³) / Σ(capacità)",
            "Produzione eolica nazionale"
        )
    except Exception as e:
        return handle_error(e)


@incroci_esteso_bp.route("/scatter-indice-solare-produzione-fotovoltaica")
def scatter_indice_solare_produzione_fotovoltaica():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH capacita_fotovoltaica AS (
            SELECT
                c.anno, c.mese, c.provincia_id,
                SUM(c.potenza_nominale) AS capacita_fv
            FROM capacita_installate c
            INNER JOIN fonti_energetiche f ON c.fonte_id = f.id
            WHERE c.anno = %s AND f.nome = 'Photovoltaic'
            GROUP BY c.anno, c.mese, c.provincia_id
        ),
        indice_solare_orario AS (
            SELECT
                m.data, m.orario,
                SUM(m.radiazione * c.capacita_fv)
                    / NULLIF(SUM(c.capacita_fv), 0) AS indice_solare
            FROM meteo m
            INNER JOIN capacita_fotovoltaica c
                ON m.provincia_id = c.provincia_id
               AND YEAR(m.data) = c.anno
               AND MONTH(m.data) = c.mese
            WHERE YEAR(m.data) = %s
              AND m.radiazione IS NOT NULL
              AND m.radiazione > 20
            GROUP BY m.data, m.orario
        ),
        produzione_fotovoltaica AS (
            SELECT
                p.data, p.orario,
                SUM(p.generazione) AS produzione_fv
            FROM produzioni p
            INNER JOIN fonti_energetiche f ON p.fonte_id = f.id
            WHERE YEAR(p.data) = %s AND f.nome = 'Photovoltaic'
            GROUP BY p.data, p.orario
        )
        SELECT
            i.data, i.orario, i.indice_solare, p.produzione_fv
        FROM indice_solare_orario i
        INNER JOIN produzione_fotovoltaica p
            ON i.data = p.data AND i.orario = p.orario
        WHERE i.indice_solare IS NOT NULL
          AND p.produzione_fv IS NOT NULL
        ORDER BY i.data, i.orario
    """

    try:
        return _grafico_scatter_generico(
            query,
            [anno_int, anno_int, anno_int],
            "indice_solare",
            "produzione_fv",
            f"Indice solare vs produzione fotovoltaica - {anno_int}",
            "Radiazione nazionale pesata per capacità fotovoltaica",
            "Produzione fotovoltaica nazionale"
        )
    except Exception as e:
        return handle_error(e)


# ============================================================
# GRAFICI A PANNELLI PER ZONA
# ============================================================

@incroci_esteso_bp.route("/grafico-domanda-per-fasce-temperatura-pannelli")
def grafico_domanda_per_fasce_temperatura_pannelli():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))
    zona = request.args.get("zona")

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH temperatura_oraria AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data, m.orario,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            INNER JOIN province p ON m.provincia_id = p.id
            INNER JOIN regioni r ON p.regione_id = r.id
            INNER JOIN bidding_zones z ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s AND m.temperatura IS NOT NULL
            GROUP BY z.id, z.nome, m.data, m.orario
        ),
        domanda_oraria AS (
            SELECT
                d.zona_id, d.data, d.orario,
                AVG(d.domanda_effettiva) AS domanda_effettiva
            FROM domande d
            WHERE YEAR(d.data) = %s AND d.domanda_effettiva IS NOT NULL
            GROUP BY d.zona_id, d.data, d.orario
        ),
        dati_completi AS (
            SELECT
                t.zona_id, t.zona, t.data, t.orario,
                t.temperatura_media, d.domanda_effettiva,
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
            ROUND(AVG(temperatura_media), 2) AS temperatura_media,
            ROUND(AVG(domanda_effettiva), 2) AS domanda_effettiva_media
        FROM dati_completi
    """

    parametri = [anno_int, anno_int]

    if zona:
        query += " WHERE zona = %s"
        parametri.append(zona)

    query += " GROUP BY zona, fascia_temperatura"

    try:
        risultati = execute_query(query, parametri)

        df = pd.DataFrame(risultati)

        if df.empty:
            return jsonify({"errore": "Nessun dato disponibile."}), 404

        df["domanda_effettiva_media"] = df["domanda_effettiva_media"].astype(float)
        df["temperatura_media"] = df["temperatura_media"].astype(float)
        df["numero_osservazioni"] = df["numero_osservazioni"].astype(int)

        ordine_fasce = [
            "sotto_-5", "-5_0", "0_5", "5_10", "10_15",
            "15_20", "20_25", "25_30", "sopra_30"
        ]

        etichette = [
            "< -5", "-5 / 0", "0 / 5", "5 / 10", "10 / 15",
            "15 / 20", "20 / 25", "25 / 30", "> 30"
        ]

        x_pos = list(range(len(ordine_fasce)))

        zone = sorted(df["zona"].unique())
        n_zone = len(zone)

        if n_zone == 1:
            fig, ax = plt.subplots(figsize=(11, 7))
            axes = [ax]
        else:
            fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(15, 16))
            axes = axes.flatten()

        for i, nome_zona in enumerate(zone):

            dati_zona = df[df["zona"] == nome_zona].copy()
            dati_zona = (
                dati_zona.set_index("fascia_temperatura").reindex(ordine_fasce)
            )

            y = dati_zona["domanda_effettiva_media"].to_numpy(dtype=float)
            n = dati_zona["numero_osservazioni"]

            axes[i].plot(x_pos, y, marker="o", linewidth=2)
            axes[i].set_title(nome_zona, fontsize=13)
            axes[i].set_xticks(x_pos)
            axes[i].set_xticklabels(etichette, rotation=45, ha="right")
            axes[i].set_xlabel("Fascia di temperatura (°C)")
            axes[i].set_ylabel("Domanda elettrica media")
            axes[i].grid(axis="y", alpha=0.3)

            for j in range(len(ordine_fasce)):

                valore_y = y[j]
                numero_obs = n.iloc[j]

                if not pd.isna(valore_y) and not pd.isna(numero_obs):
                    axes[i].annotate(
                        f"n={int(numero_obs)}",
                        (x_pos[j], valore_y),
                        textcoords="offset points",
                        xytext=(0, 8),
                        ha="center",
                        fontsize=8
                    )

        if n_zone > 1:
            for j in range(n_zone, len(axes)):
                fig.delaxes(axes[j])

        titolo = f"Domanda elettrica media per fascia di temperatura - {anno_int}"

        if zona:
            titolo += f" - {zona}"

        fig.suptitle(titolo, fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)


@incroci_esteso_bp.route("/grafico-temperatura-domanda-procapite")
def grafico_temperatura_domanda_procapite():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))
    zona = request.args.get("zona")

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    data_inizio = f"{anno_int}-01-01"
    data_fine = f"{anno_int + 1}-01-01"

    query = """
        WITH dati_zona AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                SUM(dp.popolazione) AS popolazione_zona,
                COUNT(DISTINCT dp.provincia_id) AS numero_province
            FROM dati_province dp
            INNER JOIN province p ON dp.provincia_id = p.id
            INNER JOIN regioni r ON p.regione_id = r.id
            INNER JOIN bidding_zones z ON r.zona_id = z.id
            WHERE dp.anno = %s
            GROUP BY z.id, z.nome
        ),
        temperatura_provincia AS (
            SELECT
                m.data, m.orario, m.provincia_id,
                AVG(m.temperatura) AS temperatura_provincia
            FROM meteo m
            WHERE m.data >= %s AND m.data < %s AND m.temperatura IS NOT NULL
            GROUP BY m.data, m.orario, m.provincia_id
        ),
        temperatura_zona AS (
            SELECT
                z.id AS zona_id, z.nome AS zona,
                t.data, t.orario,
                AVG(t.temperatura_provincia) AS temperatura_media
            FROM temperatura_provincia t
            INNER JOIN province p ON t.provincia_id = p.id
            INNER JOIN regioni r ON p.regione_id = r.id
            INNER JOIN bidding_zones z ON r.zona_id = z.id
            GROUP BY z.id, z.nome, t.data, t.orario
        ),
        domanda_zona AS (
            SELECT
                d.zona_id, d.data, d.orario,
                AVG(d.domanda_effettiva) AS domanda_effettiva
            FROM domande d
            WHERE d.data >= %s AND d.data < %s
              AND d.domanda_effettiva IS NOT NULL
            GROUP BY d.zona_id, d.data, d.orario
        )
        SELECT
            t.zona, t.data, t.orario,
            t.temperatura_media, d.domanda_effettiva,
            dz.popolazione_zona, dz.numero_province,
            (
                d.domanda_effettiva
                / NULLIF(dz.popolazione_zona, 0)
                * 1000000
            ) AS domanda_per_milione
        FROM temperatura_zona t
        INNER JOIN domanda_zona d
            ON t.zona_id = d.zona_id
           AND t.data = d.data
           AND t.orario = d.orario
        INNER JOIN dati_zona dz ON t.zona_id = dz.zona_id
    """

    parametri = [anno_int, data_inizio, data_fine, data_inizio, data_fine]

    if zona:
        query += " WHERE t.zona = %s"
        parametri.append(zona)

    try:
        risultati = execute_query(query, parametri)

        df = pd.DataFrame(risultati)

        if df.empty:
            return jsonify({"errore": "Nessun dato disponibile."}), 404

        for colonna in [
            "temperatura_media", "domanda_effettiva",
            "popolazione_zona", "domanda_per_milione"
        ]:
            df[colonna] = df[colonna].astype(float)

        df["numero_province"] = df["numero_province"].astype(int)

        df = df.dropna(subset=["temperatura_media", "domanda_per_milione"])

        zone = sorted(df["zona"].unique())
        n_zone = len(zone)

        if n_zone == 1:
            fig, ax = plt.subplots(figsize=(10, 7))
            axes = [ax]
        else:
            ncols = 2
            nrows = int(np.ceil(n_zone / ncols))
            fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 5 * nrows))
            axes = np.array(axes).reshape(-1)

        for i, nome_zona in enumerate(zone):

            dati_zona = df[df["zona"] == nome_zona].copy()

            x = dati_zona["temperatura_media"].to_numpy(dtype=float)
            y = dati_zona["domanda_per_milione"].to_numpy(dtype=float)

            pearson = pd.Series(x).corr(pd.Series(y), method="pearson")
            spearman = pd.Series(x).corr(pd.Series(y), method="spearman")

            dati_plot = (
                dati_zona.sample(n=5000, random_state=42)
                if len(dati_zona) > 5000
                else dati_zona
            )

            axes[i].scatter(
                dati_plot["temperatura_media"],
                dati_plot["domanda_per_milione"],
                alpha=0.18,
                s=10
            )

            r2_quad = np.nan
            temperatura_minimo = np.nan

            if len(x) >= 3:

                coeff_quad = np.polyfit(x, y, 2)
                funzione_quad = np.poly1d(coeff_quad)

                x_linea = np.linspace(x.min(), x.max(), 250)
                y_linea = funzione_quad(x_linea)

                axes[i].plot(x_linea, y_linea, linewidth=2.5)

                y_pred = funzione_quad(x)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)

                if ss_tot != 0:
                    r2_quad = 1 - ss_res / ss_tot

                a, b = coeff_quad[0], coeff_quad[1]

                if a > 0:

                    t_vertice = -b / (2 * a)

                    if x.min() <= t_vertice <= x.max():

                        temperatura_minimo = t_vertice
                        domanda_minima = funzione_quad(temperatura_minimo)

                        axes[i].scatter(
                            [temperatura_minimo], [domanda_minima], s=55, zorder=5
                        )
                        axes[i].axvline(
                            temperatura_minimo, linestyle="--", alpha=0.5
                        )

            popolazione = int(dati_zona["popolazione_zona"].iloc[0])
            numero_province = int(dati_zona["numero_province"].iloc[0])

            testo = (
                f"n = {len(dati_zona):,}\n"
                f"Province = {numero_province}\n"
                f"Pop. = {popolazione / 1_000_000:.2f} M\n"
                f"Pearson = {pearson:.3f}\n"
                f"Spearman = {spearman:.3f}\n"
                f"R² quad = {r2_quad:.3f}"
            )

            if not np.isnan(temperatura_minimo):
                testo += f"\nT minimo = {temperatura_minimo:.1f} °C"

            axes[i].text(
                0.03, 0.97, testo,
                transform=axes[i].transAxes,
                verticalalignment="top",
                fontsize=9,
                bbox=dict(boxstyle="round", alpha=0.15)
            )

            axes[i].set_title(nome_zona, fontsize=13)
            axes[i].set_xlabel("Temperatura media delle province (°C)")
            axes[i].set_ylabel("Domanda elettrica (MW per milione di abitanti)")
            axes[i].grid(alpha=0.25)

        if n_zone > 1:
            for j in range(n_zone, len(axes)):
                fig.delaxes(axes[j])

        titolo = (
            f"Temperatura media e domanda elettrica per milione di abitanti - {anno_int}"
        )

        if zona:
            titolo += f" - {zona}"

        fig.suptitle(titolo, fontsize=17)
        plt.tight_layout(rect=[0, 0, 1, 0.97])

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)


# ============================================================
# TEST STATISTICO KRUSKAL-WALLIS
# ============================================================

@incroci_esteso_bp.route("/test-temperatura-errore-previsione")
def test_temperatura_errore_previsione():

    anno_int = _anno_valido(request.args.get("anno", default="2025"))
    zona = request.args.get("zona")

    if anno_int is None:
        return jsonify({"errore": "Formato anno non valido. Usa YYYY."}), 400

    query = """
        WITH temperatura_giornaliera AS (
            SELECT
                z.id AS zona_id,
                z.nome AS zona,
                m.data,
                AVG(m.temperatura) AS temperatura_media
            FROM meteo m
            INNER JOIN province p ON m.provincia_id = p.id
            INNER JOIN regioni r ON p.regione_id = r.id
            INNER JOIN bidding_zones z ON r.zona_id = z.id
            WHERE YEAR(m.data) = %s AND m.temperatura IS NOT NULL
            GROUP BY z.id, z.nome, m.data
        ),
        temperatura_classificata AS (
            SELECT
                zona_id, zona, data, temperatura_media,
                NTILE(10) OVER (
                    PARTITION BY zona_id ORDER BY temperatura_media
                ) AS decile_temperatura
            FROM temperatura_giornaliera
        ),
        domanda_giornaliera AS (
            SELECT
                d.zona_id, d.data,
                AVG(d.domanda_effettiva) AS domanda_effettiva,
                AVG(ABS(d.domanda_effettiva - d.domanda_prevista))
                    AS errore_assoluto
            FROM domande d
            WHERE YEAR(d.data) = %s
              AND d.domanda_effettiva IS NOT NULL
              AND d.domanda_prevista IS NOT NULL
            GROUP BY d.zona_id, d.data
        )
        SELECT
            t.zona, t.data,
            CASE
                WHEN t.decile_temperatura IN (1, 2) THEN 'freddo_estremo'
                WHEN t.decile_temperatura IN (9, 10) THEN 'caldo_estremo'
                ELSE 'normale'
            END AS tipo_periodo,
            (
                d.errore_assoluto
                / NULLIF(ABS(d.domanda_effettiva), 0)
                * 100
            ) AS errore_percentuale
        FROM temperatura_classificata t
        INNER JOIN domanda_giornaliera d
            ON t.zona_id = d.zona_id AND t.data = d.data
        WHERE d.domanda_effettiva != 0
    """

    parametri = [anno_int, anno_int]

    if zona:
        query += " AND t.zona = %s"
        parametri.append(zona)

    try:
        risultati = execute_query(query, parametri)

        df = pd.DataFrame(risultati)

        if df.empty:
            return jsonify({"errore": "Nessun dato disponibile."}), 404

        df["errore_percentuale"] = df["errore_percentuale"].astype(float)

        risultati_test = []

        for nome_zona in df["zona"].unique():

            dati_zona = df[df["zona"] == nome_zona]

            freddo = dati_zona[
                dati_zona["tipo_periodo"] == "freddo_estremo"
            ]["errore_percentuale"]

            normale = dati_zona[
                dati_zona["tipo_periodo"] == "normale"
            ]["errore_percentuale"]

            caldo = dati_zona[
                dati_zona["tipo_periodo"] == "caldo_estremo"
            ]["errore_percentuale"]

            if len(freddo) > 0 and len(normale) > 0 and len(caldo) > 0:

                statistica, p_value = kruskal(freddo, normale, caldo)

                risultati_test.append({
                    "zona": nome_zona,
                    "n_freddo": len(freddo),
                    "n_normale": len(normale),
                    "n_caldo": len(caldo),
                    "errore_mediano_freddo": round(freddo.median(), 3),
                    "errore_mediano_normale": round(normale.median(), 3),
                    "errore_mediano_caldo": round(caldo.median(), 3),
                    "statistica_H": round(float(statistica), 3),
                    "p_value": round(float(p_value), 6),
                    "significativo_005": bool(p_value < 0.05)
                })

        return jsonify({
            "anno": anno_int,
            "test": "Kruskal-Wallis",
            "ipotesi_nulla":
                "La distribuzione dell'errore di previsione è uguale "
                "nei periodi freddi, normali e caldi.",
            "soglia_significativita": 0.05,
            "risultati": risultati_test
        })

    except Exception as e:
        return handle_error(e)
