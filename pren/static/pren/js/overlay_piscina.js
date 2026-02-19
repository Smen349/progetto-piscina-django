console.log("overlay_piscina.js caricato ", {
  CAN_DRAG: window.CAN_DRAG,
  CAN_BOOK: window.CAN_BOOK,
  PISCINA_ID: window.PISCINA_ID,
});

const CAN_DRAG = window.CAN_DRAG === true;
const CAN_BOOK = window.CAN_BOOK === true;

let dragging = false;
let activeEl = null;

function getCSRFToken() {
  const cookieValue = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="));
  return cookieValue ? cookieValue.split("=")[1] : "";
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function salvaPosizione(el) {
  if (!el) return;
  const leftPercent = parseFloat(el.style.left);
  const topPercent = parseFloat(el.style.top);

  fetch(`/sdrai/${el.dataset.id}/aggiorna/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
    body: JSON.stringify({ x_percentuale: leftPercent, y_percentuale: topPercent }),
  }).catch(() => {});
}

function eliminaSdraio(id) {
  return fetch(`/sdrai/${id}/elimina/`, {
    method: "POST",
    headers: { "X-CSRFToken": getCSRFToken() },
  });
}

function rigeneraSdrai() {
  if (!window.PISCINA_ID) {
    alert("Errore: PISCINA_ID non definito.");
    return;
  }
  return fetch(`/rigenera/${window.PISCINA_ID}/`, {
    method: "POST",
    headers: { "X-CSRFToken": getCSRFToken() },
  }).then(async (r) => {
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("overlay-piscina");
  if (!overlay) return;

  const sdrai = overlay.querySelectorAll(".sdraio");
  sdrai.forEach((el) => {
    el.style.userSelect = "none";
    el.style.touchAction = "none";
    if (CAN_DRAG) el.style.cursor = "grab";
  });

  // ===== Pulsante admin: rigenera sdrai =====
  if (CAN_DRAG) {
    const btn = document.getElementById("btn-rigenera");
    if (btn) {
      btn.addEventListener("click", async () => {
        const ok = confirm("Vuoi cancellare TUTTI gli sdrai e rigenerarli con AI?");
        if (!ok) return;

        try {
          const data = await rigeneraSdrai();
          alert(`Rigenerazione completata \nCreati: ${data.creati ?? "?"}`);
          location.reload();
        } catch (e) {
          alert("Errore rigenerazione: " + e.message);
        }
      });
    }
  }

  // ===== DRAG immediato (admin) con Pointer Events =====
  if (CAN_DRAG && "PointerEvent" in window) {
    sdrai.forEach((el) => {
      el.addEventListener("pointerdown", (e) => {
        if (e.pointerType === "mouse" && e.button !== 0) return;

        e.preventDefault();
        e.stopPropagation();

        activeEl = el;
        dragging = true;

        // selezione visiva
        sdrai.forEach((x) => x.classList.remove("selezionata"));
        activeEl.classList.add("selezionata");

        activeEl.style.cursor = "grabbing";
        document.body.style.userSelect = "none";

        // cattura puntatore
        try {
          activeEl.setPointerCapture(e.pointerId);
        } catch (_) {}

        const rect = overlay.getBoundingClientRect();

        const moveTo = (cx, cy) => {
          const x = cx - rect.left;
          const y = cy - rect.top;

          let left = (x / rect.width) * 100;
          let top = (y / rect.height) * 100;

          left = clamp(left, 0, 100);
          top = clamp(top, 0, 100);

          activeEl.style.left = left.toFixed(4) + "%";
          activeEl.style.top = top.toFixed(4) + "%";
        };

        const onMove = (ev) => {
          ev.preventDefault();
          moveTo(ev.clientX, ev.clientY);
        };

        const onUp = async (ev) => {
          ev.preventDefault();

          activeEl.removeEventListener("pointermove", onMove);
          activeEl.removeEventListener("pointerup", onUp);
          activeEl.removeEventListener("pointercancel", onUp);

          try {
            activeEl.releasePointerCapture(ev.pointerId);
          } catch (_) {}

          document.body.style.userSelect = "";

          // controlla cestino
          const trash = document.getElementById("trash-area");
          if (trash) {
            const tr = trash.getBoundingClientRect();
            const inTrash =
              ev.clientX >= tr.left &&
              ev.clientX <= tr.right &&
              ev.clientY >= tr.top &&
              ev.clientY <= tr.bottom;

            if (inTrash) {
              try {
                await eliminaSdraio(activeEl.dataset.id);
                location.reload();
                return;
              } catch (_) {
                alert("Errore eliminazione sdraio.");
              }
            }
          }

          activeEl.style.cursor = "grab";

          // evita dblclick “fantasma”
          setTimeout(() => {
            dragging = false;
          }, 180);

          salvaPosizione(activeEl);
          activeEl = null;
        };

        activeEl.addEventListener("pointermove", onMove);
        activeEl.addEventListener("pointerup", onUp);
        activeEl.addEventListener("pointercancel", onUp);
      });
    });
  }

  // ===== PRENOTAZIONE (utente normale) =====
  if (CAN_BOOK) {
    overlay.addEventListener("dblclick", (e) => {
      if (dragging) return;

      const sdraio = e.target.closest(".sdraio");
      if (!sdraio) return;

      e.preventDefault();
      e.stopPropagation();

      const tipoDurata = document.getElementById("tipo_durata")?.value;
      const inizio = document.getElementById("inizio")?.value;

      if (!tipoDurata || !inizio) {
        alert("Seleziona durata e data/ora prima di prenotare.");
        return;
      }

      fetch(`/prenota/${sdraio.dataset.id}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-CSRFToken": getCSRFToken(),
        },
        body: new URLSearchParams({ tipo_durata: tipoDurata, inizio }),
      })
        .then((resp) => resp.ok ? resp.text() : resp.text().then((t) => { throw new Error(t); }))
        .then(() => {
          alert("Prenotazione salvata");
          location.reload();
        })
        .catch((err) => {
          alert("Errore prenotazione: " + err.message);
        });
    });
  }
});
