/*
    Script per _carosello.html.
    Da collegare in index.html con:
    <script src="{{ url_for('static', filename='script_carosello.js') }}" defer></script>
*/

const caroselloTrack = document.querySelector(".carosello-track");

if (caroselloTrack) {

    const slides = Array.from(
        caroselloTrack.querySelectorAll(".carosello-slide")
    );

    const puntiniContainer = document.querySelector(".carosello-puntini");
    const btnPrecedente = document.querySelector(".carosello-prec");
    const btnSuccessiva = document.querySelector(".carosello-succ");

    let indiceAttuale = 0;
    let timerAuto = null;

    slides.forEach((slide, indice) => {

        const puntino = document.createElement("button");
        puntino.type = "button";
        puntino.className = "carosello-puntino";

        if (indice === 0) {
            puntino.classList.add("attivo");
        }

        puntino.setAttribute("aria-label", `Vai all'immagine ${indice + 1}`);

        puntino.addEventListener("click", () => vaiA(indice));

        puntiniContainer.appendChild(puntino);
    });

    const puntini = Array.from(
        puntiniContainer.querySelectorAll(".carosello-puntino")
    );

    function vaiA(indice) {

        slides[indiceAttuale].classList.remove("attiva");
        puntini[indiceAttuale].classList.remove("attivo");

        indiceAttuale = (indice + slides.length) % slides.length;

        slides[indiceAttuale].classList.add("attiva");
        puntini[indiceAttuale].classList.add("attivo");

        riavviaTimer();
    }

    function avanti() {
        vaiA(indiceAttuale + 1);
    }

    function indietro() {
        vaiA(indiceAttuale - 1);
    }

    function riavviaTimer() {

        if (timerAuto) {
            clearInterval(timerAuto);
        }

        timerAuto = setInterval(avanti, 5000);
    }

    if (btnSuccessiva) {
        btnSuccessiva.addEventListener("click", avanti);
    }

    if (btnPrecedente) {
        btnPrecedente.addEventListener("click", indietro);
    }

    const caroselloSection = document.querySelector(".carosello");

    if (caroselloSection) {
        caroselloSection.addEventListener(
            "mouseenter",
            () => clearInterval(timerAuto)
        );
        caroselloSection.addEventListener("mouseleave", riavviaTimer);
    }

    riavviaTimer();
}
