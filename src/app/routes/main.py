from flask import Blueprint, jsonify, render_template

from ..db import execute_query, get_connection

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():

    province = [
        riga["nome"]
        for riga in execute_query(
            "SELECT nome FROM province ORDER BY nome"
        )
    ]

    return render_template(
        "index.html",
        province=province
    )


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
