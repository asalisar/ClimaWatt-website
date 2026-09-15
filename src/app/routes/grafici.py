import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request, send_file

from ..db import execute_query
from ..utils import get_year_range, handle_error

grafici_bp = Blueprint("grafici", __name__)


@grafici_bp.route("/grafico-temperatura-radiazione")
def grafico_temperatura_radiazione():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                CASE
                    WHEN m.temperatura < 5 THEN '<5'
                    WHEN m.temperatura >= 5
                         AND m.temperatura < 10 THEN '5-10'
                    WHEN m.temperatura >= 10
                         AND m.temperatura < 15 THEN '10-15'
                    WHEN m.temperatura >= 15
                         AND m.temperatura < 20 THEN '15-20'
                    WHEN m.temperatura >= 20
                         AND m.temperatura < 25 THEN '20-25'
                    WHEN m.temperatura >= 25
                         AND m.temperatura < 30 THEN '25-30'
                    ELSE '>30'
                END AS classe_temperatura,

                CASE
                    WHEN m.radiazione = 0 THEN '0'
                    WHEN m.radiazione > 0
                         AND m.radiazione <= 200 THEN '1-200'
                    WHEN m.radiazione > 200
                         AND m.radiazione <= 400 THEN '200-400'
                    WHEN m.radiazione > 400
                         AND m.radiazione <= 600 THEN '400-600'
                    WHEN m.radiazione > 600
                         AND m.radiazione <= 800 THEN '600-800'
                    ELSE '>800'
                END AS classe_radiazione,

                COUNT(*) AS ore

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
            GROUP BY
                classe_temperatura,
                classe_radiazione
        """

        risultati = execute_query(query, params)

        if not risultati:
            return jsonify({
                "errore": "Nessun dato disponibile per i parametri selezionati."
            }), 404

        df = pd.DataFrame(risultati)

        pivot = df.pivot_table(
            index="classe_temperatura",
            columns="classe_radiazione",
            values="ore",
            aggfunc="sum",
            fill_value=0
        )

        pivot = pivot.div(
            pivot.sum(axis=1),
            axis=0
        ) * 100

        ordine_temperatura = [
            "<5", "5-10", "10-15", "15-20", "20-25", "25-30", ">30"
        ]

        ordine_radiazione = [
            "0", "1-200", "200-400", "400-600", "600-800", ">800"
        ]

        pivot = pivot.reindex(
            index=ordine_temperatura,
            columns=ordine_radiazione,
            fill_value=0
        )

        fig, ax = plt.subplots(figsize=(12, 7))

        pivot.plot(kind="bar", stacked=True, ax=ax)

        ax.set_title(
            f"Distribuzione della radiazione per classe di temperatura - {anno}"
        )

        ax.set_xlabel("Classe di temperatura (°C)")
        ax.set_ylabel("Percentuale delle ore (%)")

        ax.legend(
            title="Radiazione",
            bbox_to_anchor=(1.05, 1),
            loc="upper left"
        )

        plt.xticks(rotation=0)
        plt.tight_layout()

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)


@grafici_bp.route("/grafico-vento-temperatura-stagioni")
def grafico_vento_temperatura_stagioni():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                CASE
                    WHEN MONTH(m.data) IN (12, 1, 2)
                        THEN 'Inverno'
                    WHEN MONTH(m.data) IN (3, 4, 5)
                        THEN 'Primavera'
                    WHEN MONTH(m.data) IN (6, 7, 8)
                        THEN 'Estate'
                    ELSE 'Autunno'
                END AS stagione,

                CASE
                    WHEN m.temperatura < 5 THEN '<5'
                    WHEN m.temperatura >= 5
                         AND m.temperatura < 10 THEN '5-10'
                    WHEN m.temperatura >= 10
                         AND m.temperatura < 15 THEN '10-15'
                    WHEN m.temperatura >= 15
                         AND m.temperatura < 20 THEN '15-20'
                    WHEN m.temperatura >= 20
                         AND m.temperatura < 25 THEN '20-25'
                    WHEN m.temperatura >= 25
                         AND m.temperatura < 30 THEN '25-30'
                    ELSE '>30'
                END AS classe_temperatura,

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
            GROUP BY
                stagione,
                classe_temperatura
        """

        risultati = execute_query(query, params)

        if not risultati:
            return jsonify({
                "errore": "Nessun dato disponibile per i parametri selezionati."
            }), 404

        df = pd.DataFrame(risultati)

        ordine_temperatura = [
            "<5", "5-10", "10-15", "15-20", "20-25", "25-30", ">30"
        ]

        stagioni = ["Inverno", "Primavera", "Estate", "Autunno"]

        fig, ax = plt.subplots(figsize=(12, 7))

        for stagione in stagioni:

            dati = df[df["stagione"] == stagione].copy()

            dati["classe_temperatura"] = pd.Categorical(
                dati["classe_temperatura"],
                categories=ordine_temperatura,
                ordered=True
            )

            dati = dati.sort_values("classe_temperatura")

            if not dati.empty:
                ax.plot(
                    dati["classe_temperatura"],
                    dati["vento_medio"],
                    marker="o",
                    label=stagione
                )

        ax.set_title(
            f"Vento medio per classe di temperatura e stagione - {anno}"
        )

        ax.set_xlabel("Classe di temperatura (°C)")
        ax.set_ylabel("Velocità media del vento (m/s)")

        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.xticks(rotation=0)
        plt.tight_layout()

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)


@grafici_bp.route("/scatter-vento-radiazione")
def scatter_vento_radiazione():

    try:

        anno = request.args.get("anno")
        provincia = request.args.get("provincia")

        anno, data_inizio, data_fine = get_year_range(anno)

        query = """
            SELECT
                m.vento,
                m.radiazione
            FROM meteo m
            JOIN province p
                ON m.provincia_id = p.id
            WHERE m.data >= %s
              AND m.data < %s
              AND m.vento IS NOT NULL
              AND m.radiazione IS NOT NULL
              AND RAND() <= 0.05
        """

        params = [data_inizio, data_fine]

        if provincia:
            query += " AND p.nome = %s"
            params.append(provincia)

        risultati = execute_query(query, params)

        if not risultati:
            return jsonify({
                "errore": "Nessun dato disponibile per i parametri selezionati."
            }), 404

        df = pd.DataFrame(risultati)

        df["vento"] = pd.to_numeric(df["vento"], errors="coerce")
        df["radiazione"] = pd.to_numeric(df["radiazione"], errors="coerce")

        df = df.dropna(subset=["vento", "radiazione"])

        if df.empty:
            return jsonify({
                "errore": "Nessun dato numerico disponibile."
            }), 404

        pearson = df["vento"].corr(df["radiazione"], method="pearson")
        spearman = df["vento"].corr(df["radiazione"], method="spearman")

        df_plot = df.sample(min(len(df), 20000), random_state=42)

        coeff = np.polyfit(df_plot["vento"], df_plot["radiazione"], 1)
        retta = np.poly1d(coeff)

        x = np.linspace(
            df_plot["vento"].min(),
            df_plot["vento"].max(),
            100
        )

        fig, ax = plt.subplots(figsize=(10, 7))

        ax.scatter(df_plot["vento"], df_plot["radiazione"], alpha=0.25, s=10)
        ax.plot(x, retta(x), linewidth=2, label="Regressione lineare")

        ax.set_title(f"Relazione tra vento e radiazione - {anno}")
        ax.set_xlabel("Vento (m/s)")
        ax.set_ylabel("Radiazione")
        ax.legend()

        testo = f"Pearson: {pearson:.3f}\nSpearman: {spearman:.3f}"

        ax.text(
            0.02,
            0.98,
            testo,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", alpha=0.8)
        )

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        output = io.BytesIO()
        plt.savefig(output, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        output.seek(0)

        return send_file(output, mimetype="image/png")

    except Exception as e:
        return handle_error(e)
