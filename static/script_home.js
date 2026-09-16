/*
 * ==========================================
 * TEAM: click per mostrare la citazione
 * + easter egg: dopo 5 click la citazione cambia
 * ==========================================
 */

const CLICK_PER_EASTER_EGG = 5;

document.querySelectorAll(".team-card-clickable").forEach(card => {

    const citazione = card.querySelector(".team-citazione");
    const citazioneSegreta = citazione ? citazione.dataset.segreta : null;

    let numeroClick = 0;
    let easterEggSvelato = false;

    function toggleCitazione() {
        const aperta = card.getAttribute("aria-expanded") === "true";
        card.setAttribute("aria-expanded", String(!aperta));

        numeroClick++;

        if (!easterEggSvelato && citazioneSegreta && numeroClick >= CLICK_PER_EASTER_EGG) {
            easterEggSvelato = true;
            citazione.textContent = citazioneSegreta;
            card.classList.add("easter-egg-svelato");
        }
    }

    card.addEventListener("click", toggleCitazione);

    card.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            toggleCitazione();
        }
    });
});
