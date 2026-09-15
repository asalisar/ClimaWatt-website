/*
    Script per _dashboard_estesa.html.
    Da collegare in index.html con:
    <script src="{{ url_for('static', filename='script_esteso.js') }}" defer></script>
    (dopo lo <script> che carica static/script.js, cosi' puo' riusare
    la funzione formattaData() gia' definita li'.)
*/

const API_URL_ESTESO = "";

const btnAnalizzaEsteso = document.getElementById("btnAnalizzaEsteso");
const giornoEstesoInput = document.getElementById("giornoEsteso");
const meseEstesoInput = document.getElementById("meseEsteso");
const provinciaEstesoSelect = document.getElementById("provinciaEsteso");
const sogliaEstesoInput = document.getElementById("sogliaEsteso");
const sogliaVentoEstesoInput = document.getElementById("sogliaVentoEsteso");
const messaggioEsteso = document.getElementById("messaggioEsteso");

const devStdTemperatura = document.getElementById("devStdTemperatura");
const escursioneTermica = document.getElementById("escursioneTermica");
const giorniSogliaTemperatura = document.getElementById("giorniSogliaTemperatura");

const radiazioneMedia = document.getElementById("radiazioneMedia");
const radiazioneMassima = document.getElementById("radiazioneMassima");
const radiazioneCumulata = document.getElementById("radiazioneCumulata");

const oraPiuCaldaFascia = document.getElementById("oraPiuCaldaFascia");
const oraPiuFreddaFascia = document.getElementById("oraPiuFreddaFascia");
const devStdVento = document.getElementById("devStdVento");
const giorniSogliaVento = document.getElementById("giorniSogliaVento");

const giornoPiuCaldoProvinciaAnno =
    document.getElementById("giornoPiuCaldoProvinciaAnno");
const giornoPiuFreddoProvinciaAnno =
    document.getElementById("giornoPiuFreddoProvinciaAnno");
const oraPiuCaldaAnno = document.getElementById("oraPiuCaldaAnno");
const oraPiuFreddaAnno = document.getElementById("oraPiuFreddaAnno");
const meseMaxRadiazione = document.getElementById("meseMaxRadiazione");


function mediaValori(righe, campo) {
    const valori = righe
        .map(riga => Number(riga[campo]))
        .filter(valore => !isNaN(valore));

    if (valori.length === 0) {
        return null;
    }

    return valori.reduce((somma, v) => somma + v, 0) / valori.length;
}


function costruisceParametroPeriodo() {

    const giorno = giornoEstesoInput.value;
    const mese = meseEstesoInput.value;

    if (giorno) {
        return `giorno=${giorno}`;
    }

    return `mese=${mese}`;
}


async function fetchJson(url) {
    const risposta = await fetch(url);

    if (!risposta.ok) {
        return null;
    }

    return risposta.json();
}


if (btnAnalizzaEsteso) {

    btnAnalizzaEsteso.addEventListener("click", async function () {

        const parametroPeriodo = costruisceParametroPeriodo();
        const provincia = provinciaEstesoSelect.value;
        const soglia = sogliaEstesoInput.value || 30;
        const sogliaVento = sogliaVentoEstesoInput.value || 10;

        const parametroProvincia = provincia
            ? `&provincia=${encodeURIComponent(provincia)}`
            : "";

        messaggioEsteso.textContent = "Caricamento dati...";

        try {

            const [
                datiDevStdT,
                datiEscursione,
                datiSoglia,
                datiRadMedia,
                datiRadMassima,
                datiRadCumulata,
                datiFasciaOraria,
                datiDevStdVento,
                datiSogliaVento
            ] = await Promise.all([
                fetchJson(`${API_URL_ESTESO}/temperatura-deviazione-standard-periodo?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/escursione-termica-periodo?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/giorni-soglia-temperatura-periodo?${parametroPeriodo}${parametroProvincia}&soglia=${soglia}`),
                fetchJson(`${API_URL_ESTESO}/radiazione-media-giornaliera?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/radiazione-massima-giornaliera?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/radiazione-cumulata-giornaliera?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/temperatura-fascia-oraria-periodo?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/vento-deviazione-standard-periodo?${parametroPeriodo}${parametroProvincia}`),
                fetchJson(`${API_URL_ESTESO}/giorni-soglia-vento-periodo?${parametroPeriodo}${parametroProvincia}&soglia=${sogliaVento}`)
            ]);

            if (datiDevStdT) {
                const media = mediaValori(datiDevStdT, "deviazione_standard");
                devStdTemperatura.textContent =
                    media !== null ? `${media.toFixed(2)} °C` : "-- °C";
            }

            if (datiEscursione) {
                const media = mediaValori(datiEscursione, "escursione_termica");
                escursioneTermica.textContent =
                    media !== null ? `${media.toFixed(2)} °C` : "-- °C";
            }

            if (datiSoglia) {
                giorniSogliaTemperatura.textContent =
                    datiSoglia.giorni !== undefined
                        ? `${datiSoglia.giorni}`
                        : "--";
            }

            if (datiRadMedia) {
                const media = mediaValori(datiRadMedia, "radiazione_media");
                radiazioneMedia.textContent =
                    media !== null ? `${media.toFixed(1)} W/m²` : "-- W/m²";
            }

            if (datiRadMassima) {
                const valori = datiRadMassima
                    .map(r => Number(r.radiazione_massima))
                    .filter(v => !isNaN(v));

                radiazioneMassima.textContent =
                    valori.length > 0
                        ? `${Math.max(...valori).toFixed(1)} W/m²`
                        : "-- W/m²";
            }

            if (datiRadCumulata) {
                const valori = datiRadCumulata
                    .map(r => Number(r.radiazione_cumulata))
                    .filter(v => !isNaN(v));

                const totale = valori.reduce((s, v) => s + v, 0);

                radiazioneCumulata.textContent =
                    valori.length > 0
                        ? `${totale.toFixed(0)} W/m²`
                        : "-- W/m²";
            }

            if (datiFasciaOraria && datiFasciaOraria.length > 0) {

                const conValore = datiFasciaOraria
                    .map(r => ({
                        ora: r.ora,
                        temperatura: Number(r.temperatura_media)
                    }))
                    .filter(r => !isNaN(r.temperatura));

                if (conValore.length > 0) {

                    const calda = conValore.reduce(
                        (a, b) => (b.temperatura > a.temperatura ? b : a)
                    );

                    const fredda = conValore.reduce(
                        (a, b) => (b.temperatura < a.temperatura ? b : a)
                    );

                    oraPiuCaldaFascia.textContent =
                        `${String(calda.ora).padStart(2, "0")}:00`;

                    oraPiuFreddaFascia.textContent =
                        `${String(fredda.ora).padStart(2, "0")}:00`;
                }
            }

            if (datiDevStdVento) {
                const media = mediaValori(datiDevStdVento, "deviazione_standard");
                devStdVento.textContent =
                    media !== null ? `${media.toFixed(2)} m/s` : "-- m/s";
            }

            if (datiSogliaVento) {
                giorniSogliaVento.textContent =
                    datiSogliaVento.giorni !== undefined
                        ? `${datiSogliaVento.giorni}`
                        : "--";
            }

            messaggioEsteso.textContent = "Dati aggiornati.";

        } catch (errore) {
            console.error(errore);
            messaggioEsteso.textContent =
                "Errore nel collegamento con il server Flask.";
        }
    });
}


async function caricaStatisticheAnnuali() {

    try {

        const datiCaldo = await fetchJson(
            `${API_URL_ESTESO}/gg-piu-caldo-provincia?anno=2025`
        );

        if (datiCaldo && datiCaldo.length > 0) {
            const riga = datiCaldo[0];
            giornoPiuCaldoProvinciaAnno.textContent =
                `${formattaData(riga.data)} — ${riga.provincia}`;
        }

        const datiFreddo = await fetchJson(
            `${API_URL_ESTESO}/gg-piu-freddo-provincia?anno=2025`
        );

        if (datiFreddo && datiFreddo.length > 0) {
            const riga = datiFreddo[0];
            giornoPiuFreddoProvinciaAnno.textContent =
                `${formattaData(riga.data)} — ${riga.provincia}`;
        }

    } catch (errore) {
        console.error(errore);
    }
}


async function caricaStatisticheProvincia() {

    const provincia = provinciaEstesoSelect.value;

    if (!provincia) {
        oraPiuCaldaAnno.textContent = "Seleziona una provincia";
        oraPiuFreddaAnno.textContent = "Seleziona una provincia";
        meseMaxRadiazione.textContent = "Seleziona una provincia";
        return;
    }

    const parametroProvincia = `&provincia=${encodeURIComponent(provincia)}`;

    try {

        const datiOraCalda = await fetchJson(
            `${API_URL_ESTESO}/ora-piu-calda-anno-provincia?anno=2025${parametroProvincia}`
        );

        if (datiOraCalda && datiOraCalda.ora !== undefined) {
            oraPiuCaldaAnno.textContent =
                `${String(datiOraCalda.ora).padStart(2, "0")}:00`;
        } else {
            oraPiuCaldaAnno.textContent = "--:--";
        }

        const datiOraFredda = await fetchJson(
            `${API_URL_ESTESO}/ora-piu-fredda-provincia?anno=2025${parametroProvincia}`
        );

        if (datiOraFredda && datiOraFredda.ora !== undefined) {
            oraPiuFreddaAnno.textContent =
                `${String(datiOraFredda.ora).padStart(2, "0")}:00`;
        } else {
            oraPiuFreddaAnno.textContent = "--:--";
        }

        const datiMeseRadiazione = await fetchJson(
            `${API_URL_ESTESO}/mese-max-radiazione-provincia?anno=2025${parametroProvincia}`
        );

        if (datiMeseRadiazione && datiMeseRadiazione.mese !== undefined) {
            meseMaxRadiazione.textContent =
                NOMI_MESI_ESTESO[datiMeseRadiazione.mese - 1] || "--";
        } else {
            meseMaxRadiazione.textContent = "--";
        }

    } catch (errore) {
        console.error(errore);
    }
}


const NOMI_MESI_ESTESO = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
];


if (provinciaEstesoSelect) {
    provinciaEstesoSelect.addEventListener("change", caricaStatisticheProvincia);
    caricaStatisticheAnnuali();
    caricaStatisticheProvincia();
}
