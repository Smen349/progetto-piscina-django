console.log("overlay_piscina.js caricato");

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
