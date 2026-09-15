from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def create_app():
    load_dotenv(BASE_DIR / ".env")

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.json.sort_keys = False

    from .routes.main import main_bp
    from .routes.meteo import meteo_bp
    from .routes.grafici import grafici_bp
    from .routes.domanda import domanda_bp
    from .routes.produzione import produzione_bp
    from .routes.capacita import capacita_bp
    from .routes.incroci import incroci_bp
    from .routes.esteso import esteso_bp
    from .routes.incroci_esteso import incroci_esteso_bp

    for blueprint in (
        main_bp,
        meteo_bp,
        grafici_bp,
        domanda_bp,
        produzione_bp,
        capacita_bp,
        incroci_bp,
        esteso_bp,
        incroci_esteso_bp,
    ):
        app.register_blueprint(blueprint)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"errore": "Endpoint non trovato."}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"errore": "Errore interno del server."}), 500

    return app
