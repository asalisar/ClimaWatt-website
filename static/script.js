// URL relativo: funziona sia in locale sia se un domani il progetto
// viene ospitato altrove, perché la pagina e le API sono sempre
// servite dallo stesso Flask, quindi niente problemi di CORS.
const API_URL = "";

const btnAnalizza = document.getElementById("btnAnalizza");
const meseInput = document.getElementById("mese");
const provinciaSelect = document.getElementById("provincia");

const temperaturaMedia = document.getElementById("temperaturaMedia");
const temperaturaMassima = document.getElementById("temperaturaMassima");
const temperaturaMinima = document.getElementById("temperaturaMinima");

const messaggio = document.getElementById("messaggio");

btnAnalizza.addEventListener("click", async function () {

    const mese = meseInput.value;
    const provincia = provinciaSelect.value;

    if (!mese) {
        messaggio.textContent = "Seleziona un mese.";
        return;
    }

    messaggio.textContent = "Caricamento dati...";

    temperaturaMedia.textContent = "-- °C";
    temperaturaMassima.textContent = "-- °C";
    temperaturaMinima.textContent = "-- °C";

    try {

        let parametroProvincia = "";
        if (provincia) {
            parametroProvincia = `&provincia=${encodeURIComponent(provincia)}`;
        }

        const rispostaMensile = await fetch(
            `${API_URL}/temperatura-media-max-mensile?mese=${mese}${parametroProvincia}`
        );

        if (!rispostaMensile.ok) {
            throw new Error("Errore nella richiesta della temperatura mensile.");
        }

        const datiMensili = await rispostaMensile.json();

        const rispostaMinima = await fetch(
            `${API_URL}/temperatura-minima-giornaliera?mese=${mese}${parametroProvincia}`
        );

        if (!rispostaMinima.ok) {
            throw new Error("Errore nella richiesta della temperatura minima.");
        }

        const datiMinimi = await rispostaMinima.json();

        if (!datiMensili.dati || datiMensili.dati.length === 0) {
            messaggio.textContent = "Nessun dato disponibile per i filtri selezionati.";
            return;
        }

        const risultatoMensile = datiMensili.dati[0];

        temperaturaMedia.textContent = `${risultatoMensile.temperatura_media} °C`;
        temperaturaMassima.textContent = `${risultatoMensile.temperatura_massima} °C`;

        if (datiMinimi.dati && datiMinimi.dati.length > 0) {
            const valoriMinimi = datiMinimi.dati
                .map(elemento => Number(elemento.temperatura_minima))
                .filter(valore => !isNaN(valore));

            if (valoriMinimi.length > 0) {
                const minimo = Math.min(...valoriMinimi);
                temperaturaMinima.textContent = `${minimo.toFixed(2)} °C`;
            }
        }

        messaggio.textContent = `Dati caricati per ${mese}.`;

    } catch (errore) {
        console.error(errore);
        messaggio.textContent = "Errore nel collegamento con il server Flask.";
    }

});
