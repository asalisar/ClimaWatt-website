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
