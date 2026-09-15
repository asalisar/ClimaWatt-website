/*
    Script per il carosello dentro la hero-card.
    Da collegare in index.html con:
    <script src="{{ url_for('static', filename='script_carosello.js') }}" defer></script>
*/

const caroselloTrack = document.querySelector(".carosello-track");

if (caroselloTrack) {

    const slides = Array.from(
        caroselloTrack.querySelectorAll(".carosello-slide")
    );

    const puntiniContainer = document.querySelector(".carosello-puntini");

    let indiceAttuale = 0;

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
    }

    function avanti() {
        vaiA(indiceAttuale + 1);
    }

    setInterval(avanti, 4000);
}
