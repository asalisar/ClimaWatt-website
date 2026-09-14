const API_URL = "";

const btnAnalizza = document.getElementById("btnAnalizza");
const meseInput = document.getElementById("mese");
const provinciaSelect = document.getElementById("provincia");

const temperaturaMedia = document.getElementById("temperaturaMedia");
const temperaturaMassima = document.getElementById("temperaturaMassima");
const temperaturaMinima = document.getElementById("temperaturaMinima");

const giornoPiuCaldo = document.getElementById("giornoPiuCaldo");
const valoreGiornoCaldo = document.getElementById("valoreGiornoCaldo");

const giornoPiuFreddo = document.getElementById("giornoPiuFreddo");
const valoreGiornoFreddo = document.getElementById("valoreGiornoFreddo");
const provinciaGiornoCaldo =
    document.getElementById("provinciaGiornoCaldo");
const provinciaGiornoFreddo =
    document.getElementById("provinciaGiornoFreddo");

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

    giornoPiuCaldo.textContent = "--";
    valoreGiornoCaldo.textContent = "-- °C";
    provinciaGiornoCaldo.textContent = "--";

    giornoPiuFreddo.textContent = "--";
    valoreGiornoFreddo.textContent = "-- °C";
    provinciaGiornoFreddo.textContent = "--";


    try {

        let parametroProvincia = "";

        if (provincia) {
            parametroProvincia =
                `&provincia=${encodeURIComponent(provincia)}`;
        }


        /*
         * 1. TEMPERATURE MEDIE GIORNALIERE
         */

        const rispostaMedie = await fetch(
            `${API_URL}/temperatura-media-giornaliera?mese=${mese}${parametroProvincia}`
        );

        if (!rispostaMedie.ok) {
            throw new Error(
                "Errore nella richiesta delle temperature medie."
            );
        }

        const datiMedie = await rispostaMedie.json();


        /*
         * 2. TEMPERATURE MASSIME GIORNALIERE
         */

        const rispostaMassime = await fetch(
            `${API_URL}/temperatura-massima-giornaliera?mese=${mese}${parametroProvincia}`
        );

        if (!rispostaMassime.ok) {
            throw new Error(
                "Errore nella richiesta delle temperature massime."
            );
        }

        const datiMassime = await rispostaMassime.json();


        /*
         * 3. TEMPERATURE MINIME GIORNALIERE
         */

        const rispostaMinime = await fetch(
            `${API_URL}/temperatura-minima-giornaliera?mese=${mese}${parametroProvincia}`
        );

        if (!rispostaMinime.ok) {
            throw new Error(
                "Errore nella richiesta delle temperature minime."
            );
        }

        const datiMinime = await rispostaMinime.json();


        if (!datiMedie || datiMedie.length === 0) {

            messaggio.textContent =
                "Nessun dato disponibile per i filtri selezionati.";

            return;
        }


        /*
         * ==========================================
         * TEMPERATURA MEDIA DEL MESE
         * ==========================================
         */

        const valoriMedie = datiMedie
            .map(elemento => Number(elemento.temperatura_media))
            .filter(valore => !isNaN(valore));


        if (valoriMedie.length > 0) {

            const mediaMensile =
                valoriMedie.reduce(
                    (somma, valore) => somma + valore,
                    0
                ) / valoriMedie.length;

            temperaturaMedia.textContent =
                `${mediaMensile.toFixed(2)} °C`;
        }


        /*
         * ==========================================
         * TEMPERATURA MASSIMA
         * ==========================================
         */

        const etichettaProvincia = provincia || "Italia (dato nazionale)";

        const valoriMassimi = datiMassime
            .map(elemento => ({
                data: elemento.data,
                provincia: etichettaProvincia,
                temperatura: Number(elemento.temperatura_massima)
            }))
            .filter(elemento => !isNaN(elemento.temperatura));

        if (valoriMassimi.length > 0) {

            const massimo = Math.max(
                ...valoriMassimi.map(
                    elemento => elemento.temperatura
                )
            );

            temperaturaMassima.textContent =
                `${massimo.toFixed(2)} °C`;


            const giornoCaldo = valoriMassimi.find(
                elemento => elemento.temperatura === massimo
            );

            if (giornoCaldo) {

                console.log("DATA GIORNO CALDO:", giornoCaldo.data);

                console.log("GIORNO CALDO:", giornoCaldo);

                giornoPiuCaldo.textContent =
                    giornoCaldo.data;

                valoreGiornoCaldo.textContent =
                    `${giornoCaldo.temperatura.toFixed(2)} °C`;

                provinciaGiornoCaldo.textContent =
                    giornoCaldo.provincia;
            }
        }


        /*
         * ==========================================
         * TEMPERATURA MINIMA
         * ==========================================
         */

        const valoriMinimi = datiMinime
            .map(elemento => ({
                data: elemento.data,
                provincia: etichettaProvincia,
                temperatura: Number(elemento.temperatura_minima)
            }))
            .filter(elemento => !isNaN(elemento.temperatura));

        if (valoriMinimi.length > 0) {

            const minimo = Math.min(
                ...valoriMinimi.map(
                    elemento => elemento.temperatura
                )
            );

            temperaturaMinima.textContent =
                `${minimo.toFixed(2)} °C`;


            const giornoFreddo = valoriMinimi.find(
                elemento => elemento.temperatura === minimo
            );


            if (giornoFreddo) {

                console.log("DATA GIORNO FREDDO:", giornoFreddo.data);

                console.log("GIORNO FREDDO:", giornoFreddo);

                giornoPiuFreddo.textContent =
                    giornoFreddo.data;

                valoreGiornoFreddo.textContent =
                    `${giornoFreddo.temperatura.toFixed(2)} °C`;

                provinciaGiornoFreddo.textContent =
                    giornoFreddo.provincia;
            }
        }


        messaggio.textContent =
            `Dati caricati per ${formattaMese(mese)}.`;


    } catch (errore) {

        console.error(errore);

        messaggio.textContent =
            "Errore nel collegamento con il server Flask.";
    }

});


function formattaMese(meseStringa) {

    const data = new Date(`${meseStringa}-01T00:00:00`);

    return data.toLocaleDateString(
        "it-IT",
        {
            month: "long",
            year: "numeric"
        }
    );
}


/*
 * ==========================================
 * EMBED DASHBOARD TABLEAU
 * ==========================================
 * Se il div #tableauViz ha un data-url impostato
 * (vedi templates/index.html), sostituisce il
 * messaggio di placeholder con la viz incorporata.
 */

const tableauContainer = document.getElementById("tableauViz");

if (tableauContainer) {

    const tableauUrl = tableauContainer.dataset.url;

    if (tableauUrl) {

        tableauContainer.innerHTML = "";

        const viz = document.createElement("tableau-viz");
        viz.setAttribute("src", tableauUrl);
        viz.setAttribute("toolbar", "bottom");

        tableauContainer.appendChild(viz);
    }
}
