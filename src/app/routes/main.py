from flask import Blueprint, jsonify, render_template

from ..db import execute_query, get_connection

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/dati")
def dati():

    province = [
        riga["nome"]
        for riga in execute_query(
            "SELECT nome FROM province ORDER BY nome"
        )
    ]

    return render_template(
        "dati.html",
        province=province
    )


@main_bp.route("/tableau")
def tableau_page():
    return render_template("tableau.html")


@main_bp.route("/api-status")
def api_status():

    try:
        connection = get_connection()
        connection.close()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "database": "disconnected",
            "errore": str(e)
        }), 500
