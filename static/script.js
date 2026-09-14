const API_URL = "";

const btnAnalizza = document.getElementById("btnAnalizza");
const meseInput = document.getElementById("mese");
const provinciaSelect = document.getElementById("provincia");

const temperaturaMedia = document.getElementById("temperaturaMedia");
const temperaturaMassima = document.getElementById("temperaturaMassima");
const temperaturaMinima = document.getElementById("temperaturaMinima");

const ventoMedio = document.getElementById("ventoMedio");
const ventoMassimo = document.getElementById("ventoMassimo");
const ventoMinimo = document.getElementById("ventoMinimo");

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

    ventoMedio.textContent = "-- m/s";
    ventoMassimo.textContent = "-- m/s";
    ventoMinimo.textContent = "-- m/s";

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

                giornoPiuCaldo.textContent =
                    formattaData(giornoCaldo.data);

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

                giornoPiuFreddo.textContent =
                    formattaData(giornoFreddo.data);

                valoreGiornoFreddo.textContent =
                    `${giornoFreddo.temperatura.toFixed(2)} °C`;

                provinciaGiornoFreddo.textContent =
                    giornoFreddo.provincia;
            }
        }


        /*
         * ==========================================
         * VENTO (media / massimo / minimo del mese)
         * ==========================================
         */

        const rispostaVentoMedio = await fetch(
            `${API_URL}/vento-medio-giornaliero?mese=${mese}${parametroProvincia}`
        );
        const rispostaVentoMassimo = await fetch(
            `${API_URL}/vento-massimo-giornaliero?mese=${mese}${parametroProvincia}`
        );
        const rispostaVentoMinimo = await fetch(
            `${API_URL}/vento-minimo-giornaliero?mese=${mese}${parametroProvincia}`
        );

        if (
            rispostaVentoMedio.ok
            && rispostaVentoMassimo.ok
            && rispostaVentoMinimo.ok
        ) {

            const datiVentoMedio = await rispostaVentoMedio.json();
            const datiVentoMassimo = await rispostaVentoMassimo.json();
            const datiVentoMinimo = await rispostaVentoMinimo.json();

            const mediaVento = datiVentoMedio
                .map(elemento => Number(elemento.vento_medio))
                .filter(valore => !isNaN(valore));

            if (mediaVento.length > 0) {
                const media = mediaVento.reduce(
                    (somma, valore) => somma + valore,
                    0
                ) / mediaVento.length;

                ventoMedio.textContent = `${media.toFixed(2)} m/s`;
            }

            const massimiVento = datiVentoMassimo
                .map(elemento => Number(elemento.vento_massimo))
                .filter(valore => !isNaN(valore));

            if (massimiVento.length > 0) {
                ventoMassimo.textContent =
                    `${Math.max(...massimiVento).toFixed(2)} m/s`;
            }

            const minimiVento = datiVentoMinimo
                .map(elemento => Number(elemento.vento_minimo))
                .filter(valore => !isNaN(valore));

            if (minimiVento.length > 0) {
                ventoMinimo.textContent =
                    `${Math.min(...minimiVento).toFixed(2)} m/s`;
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


function formattaData(dataStringa) {

    const data = new Date(dataStringa);

    return data.toLocaleDateString(
        "it-IT",
        {
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );
}


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
 * TEAM: click per mostrare la citazione
 * ==========================================
 */

document.querySelectorAll(".team-card-clickable").forEach(card => {

    function toggleCitazione() {
        const aperta = card.getAttribute("aria-expanded") === "true";
        card.setAttribute("aria-expanded", String(!aperta));
    }

    card.addEventListener("click", toggleCitazione);

    card.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            toggleCitazione();
        }
    });
});


/*
 * ==========================================
 * SEZIONE ENERGIA: domanda, produzione, capacità
 * ==========================================
 */

const NOMI_MESI = [
    "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
    "Lug", "Ago", "Set", "Ott", "Nov", "Dic"
];

const COLORE_VERDE = "#20804f";

const COLORI_FONTI = [
    "#20804f", "#2a78d6", "#eda100", "#8a5a3b",
    "#1baf7a", "#a8a29e", "#d4537e"
];

async function caricaGraficoDomandaMensile() {

    const canvas = document.getElementById("graficoDomandaMensile");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    try {

        const risposta = await fetch(
            `${API_URL}/domanda-media-mensile-nazionale?anno=2025`
        );

        const dati = await risposta.json();

        const valori = new Array(12).fill(null);

        dati.forEach(riga => {
            valori[riga.mese - 1] = Number(riga.domanda_media);
        });

        new Chart(canvas, {
            type: "line",
            data: {
                labels: NOMI_MESI,
                datasets: [{
                    label: "Domanda media (MW)",
                    data: valori,
                    borderColor: COLORE_VERDE,
                    backgroundColor: COLORE_VERDE,
                    borderWidth: 2,
                    pointRadius: 3,
                    tension: 0.25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

    } catch (errore) {
        console.error(errore);
    }
}

async function caricaGraficoProduzioneFonte() {

    const canvas = document.getElementById("graficoProduzioneFonte");
    const legenda = document.getElementById("legendaProduzioneFonte");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    try {

        const risposta = await fetch(
            `${API_URL}/percentuale-produzione-fonte`
        );

        const dati = await risposta.json();

        const colori = dati.map(
            (_, indice) => COLORI_FONTI[indice % COLORI_FONTI.length]
        );

        new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: dati.map(riga => riga.fonte),
                datasets: [{
                    data: dati.map(riga => riga.percentuale_produzione),
                    backgroundColor: colori,
                    borderColor: "#ffffff",
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });

        if (legenda) {
            legenda.innerHTML = dati.map((riga, indice) => `
                <span>
                    <span
                        class="pallino"
                        style="background:${colori[indice]}"
                    ></span>
                    ${riga.fonte} (${Number(riga.percentuale_produzione).toFixed(1)}%)
                </span>
            `).join("");
        }

    } catch (errore) {
        console.error(errore);
    }
}

async function caricaGraficoCapacitaFonte() {

    const canvas = document.getElementById("graficoCapacitaFonte");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    try {

        const risposta = await fetch(
            `${API_URL}/capacita-totale-fonte`
        );

        const dati = await risposta.json();

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: dati.map(riga => riga.fonte),
                datasets: [{
                    label: "Capacità installata (MW)",
                    data: dati.map(riga => Number(riga.capacita_totale)),
                    backgroundColor: COLORE_VERDE,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

    } catch (errore) {
        console.error(errore);
    }
}

async function caricaStatRinnovabile() {

    const contenitore = document.getElementById("statRinnovabile");

    if (!contenitore) {
        return;
    }

    try {

        const risposta = await fetch(
            `${API_URL}/produzione-rinnovabile-non-rinnovabile`
        );

        const dati = await risposta.json();

        contenitore.innerHTML = dati.map(riga => `
            <div class="stat-rinnovabile-riga">
                <span>${riga.tipo}</span>
                <strong>${Number(riga.percentuale_produzione).toFixed(1)}%</strong>
            </div>
        `).join("");

    } catch (errore) {
        console.error(errore);

        contenitore.innerHTML =
            "<p class=\"messaggio\">Dati non disponibili.</p>";
    }
}

caricaGraficoDomandaMensile();
caricaGraficoProduzioneFonte();
caricaGraficoCapacitaFonte();
caricaStatRinnovabile();


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
