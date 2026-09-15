/*
 * ==========================================
 * EMBED DASHBOARD TABLEAU
 * ==========================================
 * Se il div .tableau-viz-container ha un data-url impostato
 * (vedi templates/tableau.html), sostituisce il
 * messaggio di placeholder con la viz incorporata.
 */

document.querySelectorAll(".tableau-viz-container").forEach(function (container) {

    const tableauUrl = container.dataset.url;

    if (tableauUrl) {

        container.innerHTML = "";

        const viz = document.createElement("tableau-viz");
        viz.setAttribute("src", tableauUrl);
        viz.setAttribute("toolbar", "bottom");

        container.appendChild(viz);
    }
});
