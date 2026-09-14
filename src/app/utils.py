from datetime import datetime

from flask import jsonify


def get_year_range(anno):
    """
    Riceve un anno e restituisce:
        anno, data iniziale, data finale
    """

    try:
        anno = int(anno)

        if anno < 1900 or anno > 2100:
            raise ValueError(
                "L'anno deve essere compreso tra 1900 e 2100."
            )

        return (
            anno,
            f"{anno}-01-01",
            f"{anno + 1}-01-01"
        )

    except (TypeError, ValueError):
        raise ValueError(
            "Anno non valido. Usa un valore numerico, ad esempio 2025."
        )


def get_month_range(mese):
    """
    Riceve un mese nel formato YYYY-MM e restituisce:
        anno, data iniziale, data finale
    """

    try:
        data = datetime.strptime(mese, "%Y-%m")

        if data.month == 12:
            data_fine = datetime(data.year + 1, 1, 1)
        else:
            data_fine = datetime(data.year, data.month + 1, 1)

        return (
            data.year,
            data.strftime("%Y-%m-%d"),
            data_fine.strftime("%Y-%m-%d")
        )

    except ValueError:
        raise ValueError(
            "Formato mese non valido. Usa YYYY-MM."
        )


def get_period_range(anno=None, mese=None):
    """
    Restituisce (anno, data_inizio, data_fine) usando 'mese'
    (YYYY-MM) se presente, altrimenti 'anno' (YYYY).
    """

    if mese:
        return get_month_range(mese)

    return get_year_range(anno)


def handle_error(error):
    """Gestione standard degli errori."""

    return jsonify({
        "errore": str(error)
    }), 400
