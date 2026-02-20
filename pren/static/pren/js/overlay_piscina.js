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

function creaSdraio() {
  if (!window.PISCINA_ID) {
    alert("Errore: PISCINA_ID non definito.");
    return;
  }
  return fetch(`/sdrai/crea/${window.PISCINA_ID}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({ x_percentuale: 50.0, y_percentuale: 50.0 }),
  }).then(async (r) => {
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  });
}

/* ===== OCCUPATI ===== */
function setMinNowOnDatetimeLocal(inputEl) {
  if (!inputEl) return;
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const local = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  inputEl.min = local;
}

async function fetchOccupati(piscinaId, inizioStr, tipoDurata) {
  const url =
    `/api/occupati/${piscinaId}/?` +
    new URLSearchParams({ inizio: inizioStr, tipo_durata: tipoDurata }).toString();

  const r = await fetch(url, { method: "GET" });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.errore || "Errore nel caricamento occupati");
  return data.occupati || [];
}

function applyOccupatiToMarkers(overlay, occupatiIds) {
  const set = new Set((occupatiIds || []).map(String));
  overlay.querySelectorAll(".sdraio").forEach((el) => {
    el.classList.toggle("occupato", set.has(String(el.dataset.id)));
  });
}

function createSdraioElement(data) {
  const el = document.createElement("div");
  el.className = "sdraio manuale";
  el.dataset.id = data.id;
  el.style.left = `${data.x_percentuale}%`;
  el.style.top = `${data.y_percentuale}%`;
  el.title = data.etichetta || "Sdraio";
  el.textContent = data.etichetta || "S";
  el.style.userSelect = "none";
  el.style.touchAction = "none";
  if (CAN_DRAG) el.style.cursor = "grab";
  return el;
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

  /* ===== admin buttons ===== */
  if (CAN_DRAG) {
    const btnRig = document.getElementById("btn-rigenera");
    if (btnRig) {
      btnRig.addEventListener("click", async () => {
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

    const btnCrea = document.getElementById("btn-crea-sdraio");
    if (btnCrea) {
      btnCrea.addEventListener("click", async () => {
        try {
          const data = await creaSdraio();
          if (!data?.ok) throw new Error("Risposta non valida dal server.");

          const el = createSdraioElement(data);
          overlay.appendChild(el);

          // aggancia drag anche al nuovo elemento
          attachDragHandlers(el, overlay);

          // selezione
          overlay.querySelectorAll(".sdraio").forEach((x) => x.classList.remove("selezionata"));
          el.classList.add("selezionata");
        } catch (e) {
          alert("Errore creazione sdraio: " + e.message);
        }
      });
    }
  }

  /* ===== drag handlers ===== */
  function attachDragHandlers(el, overlayEl) {
    if (!CAN_DRAG) return;
    if (!("PointerEvent" in window)) return;

    el.addEventListener("pointerdown", (e) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;

      e.preventDefault();
      e.stopPropagation();

      activeEl = el;
      dragging = true;

      overlayEl.querySelectorAll(".sdraio").forEach((x) => x.classList.remove("selezionata"));
      activeEl.classList.add("selezionata");

      activeEl.style.cursor = "grabbing";
      document.body.style.userSelect = "none";

      try {
        activeEl.setPointerCapture(e.pointerId);
      } catch (_) {}

      const rect = overlayEl.getBoundingClientRect();

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
  }

  // attach drag to existing ones
  if (CAN_DRAG) {
    overlay.querySelectorAll(".sdraio").forEach((el) => attachDragHandlers(el, overlay));
  }

  /* ===== prenotazione + occupati live ===== */
  if (CAN_BOOK) {
    const tipoDurataEl = document.getElementById("tipo_durata");
    const inizioEl = document.getElementById("inizio");

    setMinNowOnDatetimeLocal(inizioEl);

    async function refreshOccupati() {
      const tipoDurata = tipoDurataEl?.value;
      const inizio = inizioEl?.value;

      if (!window.PISCINA_ID || !tipoDurata || !inizio) {
        applyOccupatiToMarkers(overlay, []);
        return;
      }

      try {
        const occupati = await fetchOccupati(window.PISCINA_ID, inizio, tipoDurata);
        applyOccupatiToMarkers(overlay, occupati);
      } catch (_) {
        applyOccupatiToMarkers(overlay, []);
      }
    }

    tipoDurataEl?.addEventListener("change", refreshOccupati);
    inizioEl?.addEventListener("change", refreshOccupati);
    inizioEl?.addEventListener("input", () => {
      if ((inizioEl.value || "").length >= 16) refreshOccupati();
    });

    refreshOccupati();

    overlay.addEventListener("dblclick", async (e) => {
      if (dragging) return;

      const sdraio = e.target.closest(".sdraio");
      if (!sdraio) return;

      e.preventDefault();
      e.stopPropagation();

      const tipoDurata = tipoDurataEl?.value;
      const inizio = inizioEl?.value;

      if (!tipoDurata || !inizio) {
        alert("Seleziona durata e data/ora prima di prenotare.");
        return;
      }

      if (sdraio.classList.contains("occupato")) {
        alert("Questo sdraio è già occupato nell'intervallo selezionato.");
        return;
      }

      try {
        const resp = await fetch(`/prenota/${sdraio.dataset.id}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRFToken": getCSRFToken(),
          },
          body: new URLSearchParams({ tipo_durata: tipoDurata, inizio }),
        });

        const data = await resp.json().catch(() => ({}));

        if (resp.status === 409) {
          alert(data.errore || "Sdraio già prenotato in quell'intervallo.");
          await refreshOccupati();
          return;
        }

        if (!resp.ok) {
          alert(data.errore || "Errore prenotazione.");
          await refreshOccupati();
          return;
        }

        alert("Prenotazione salvata");
        await refreshOccupati();
        location.reload();
      } catch (err) {
        alert("Errore prenotazione: " + err.message);
      }
    });
  }
});