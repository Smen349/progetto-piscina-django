let sdraioSelezionata = null;
let dragging = false;

// Permessi passati dal template
const CAN_DRAG = window.CAN_DRAG === true;
const CAN_BOOK = window.CAN_BOOK === true;

// ===== Selezione =====
document.addEventListener("click", function (e) {
    const nuova = e.target.closest(".sdraio");

    if (sdraioSelezionata && sdraioSelezionata !== nuova) {
        sdraioSelezionata.classList.remove("selezionata");
    }

    if (nuova) {
        sdraioSelezionata = nuova;
        sdraioSelezionata.classList.add("selezionata");
    } else {
        if (sdraioSelezionata) {
            sdraioSelezionata.classList.remove("selezionata");
        }
        sdraioSelezionata = null;
    }
});

// ===== Drag & Drop (solo admin) =====
document.addEventListener("mousedown", function (e) {
    if (!CAN_DRAG) return;
    if (!sdraioSelezionata) return;
    if (!sdraioSelezionata.contains(e.target)) return;

    dragging = true;

    function onMouseMove(e) {
        const overlay = document.getElementById("overlay-piscina");
        const rect = overlay.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        sdraioSelezionata.style.left = (x / rect.width) * 100 + "%";
        sdraioSelezionata.style.top = (y / rect.height) * 100 + "%";
    }

    function onMouseUp() {
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);

        // delay per evitare che il dblclick parta subito dopo drag
        setTimeout(() => {
            dragging = false;
        }, 150);

        salvaPosizione(sdraioSelezionata);
    }

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
});

// ===== Salvataggio posizione =====
function salvaPosizione(elemento) {
    const overlay = document.getElementById("overlay-piscina");
    const rect = overlay.getBoundingClientRect();

    const leftPercent = parseFloat(elemento.style.left);
    const topPercent = parseFloat(elemento.style.top);

    fetch(`/sdrai/${elemento.dataset.id}/aggiorna/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            x_percentuale: leftPercent,
            y_percentuale: topPercent
        })
    });
}

// ===== Prenotazione (solo utenti normali) =====
document.addEventListener("dblclick", function (e) {
    if (!CAN_BOOK) return;
    if (dragging) return;

    const sdraio = e.target.closest(".sdraio");
    if (!sdraio) return;

    const tipoDurata = document.getElementById("tipo_durata")?.value;
    const inizio = document.getElementById("inizio")?.value;

    if (!tipoDurata || !inizio) {
        alert("Seleziona durata e data/ora prima di prenotare.");
        return;
    }

    fetch(`/prenota/${sdraio.dataset.id}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRFToken()
        },
        body: new URLSearchParams({
            tipo_durata: tipoDurata,
            inizio: inizio
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text); });
        }
        return response.text();
    })
    .then(() => {
        alert("Prenotazione salvata");
        location.reload();
    })
    .catch(error => {
        alert("Errore prenotazione: " + error.message);
    });
});

// ===== CSRF =====
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : '';
}
