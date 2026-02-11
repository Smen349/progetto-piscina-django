
function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
            return cookie.substring(name.length + 1);
        }
    }
    return null;
}

 
function aggiornaOverlay() {
    const area = document.querySelector(".area-piscina");
    const img = document.getElementById("img-piscina");
    const overlay = document.getElementById("overlay-piscina");

    // Sicurezze
    if (!area || !img || !overlay) return;
    if (!img.naturalWidth || !img.naturalHeight) return;

    // Dimensioni contenitore
    const areaW = area.clientWidth;
    const areaH = area.clientHeight;

    // Dimensioni reali immagine
    const imgW = img.naturalWidth;
    const imgH = img.naturalHeight;

    // Rapporti
    const ratioArea = areaW / areaH;
    const ratioImg = imgW / imgH;

    let disegnataW, disegnataH;
    let offsetX = 0;
    let offsetY = 0;

    if (ratioArea > ratioImg) {
        // contenitore più largo → immagine limitata dall’altezza
        disegnataH = areaH;
        disegnataW = areaH * ratioImg;
        offsetX = (areaW - disegnataW) / 2;
    } else {
        // contenitore più stretto → immagine limitata dalla larghezza
        disegnataW = areaW;
        disegnataH = areaW / ratioImg;
        offsetY = (areaH - disegnataH) / 2;
    }

    // Applico all’overlay
    overlay.style.width = disegnataW + "px";
    overlay.style.height = disegnataH + "px";
    overlay.style.left = offsetX + "px";
    overlay.style.top = offsetY + "px";
}

window.addEventListener("load", aggiornaOverlay);
window.addEventListener("resize", aggiornaOverlay);


let sdraioSelezionata = null;

document.addEventListener("click", function (e){
    const sdraio = e.target.closest(".sdraio");
    const overlay = document.getElementById("overlay-piscina")

    if (sdraio && overlay.contains(sdraio)) {
        e.stopPropagation();

        if (sdraioSelezionata) {
            sdraioSelezionata.classList.remove("selezionata");
        }

        sdraioSelezionata = sdraio;
        sdraioSelezionata.classList.add("selezionata");

        console.log(
            "Sdraio selezionata: ",
            sdraioSelezionata.dataset.id
        );
        return;
    }

    if (sdraioSelezionata) {
        sdraioSelezionata.classList.remove("selezionata");
        sdraioSelezionata = null;
        console.log("Deselezionata");
    }
})


let dragging = false;

document.addEventListener("mousedown", function (e) {
    if(!sdraioSelezionata) return;
    if (!sdraioSelezionata.contains(e.target)) return;

    e.preventDefault();
    dragging = true;

    sdraioSelezionata.style.cursor = "grabbing";
});

document.addEventListener("mousemove", function (e) {
    if(!dragging || !sdraioSelezionata) return;

    const overlay = document.getElementById("overlay-piscina");
    const rect = overlay.getBoundingClientRect();

    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;

    x = Math.max(0, Math.min(x, rect.width));
    y = Math.max(0, Math.min(y, rect.height));

    sdraioSelezionata.style.left = x + "px";
    sdraioSelezionata.style.top = y + "px";

});

document.addEventListener("mouseup", function () {
    if (!dragging) return;

    dragging = false;

    const overlay = document.getElementById("overlay-piscina");
    const rect = overlay.getBoundingClientRect();
    //console.log("Overlay (px):", rect.width, rect.height);

    const leftPX = parseFloat(sdraioSelezionata.style.left);
    const topPX = parseFloat(sdraioSelezionata.style.top);

    //console.log("Posizione sdraio (px):", leftPX, topPX);

    const xPercentuale = (leftPX / rect.width) * 100;
    //console.log("x_percentuale:", xPercentuale);
    const yPercentuale = (topPX / rect.height) * 100;
    //console.log("y_percentuale:", yPercentuale);

    const id = sdraioSelezionata.dataset.id;

    fetch(`/sdrai/${id}/aggiorna/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            x_percentuale: xPercentuale,
            y_percentuale: yPercentuale
        })
    })

    .then(response => response.json())
    .then(data => {
        console.log("Risposta backend", data);
    })
    .catch(error => {
        console.error("Errore fetch:", error);
    });

    if (sdraioSelezionata) {
        sdraioSelezionata.style.cursor = "grab";
    }

    console.log("Drag terminato");
});
