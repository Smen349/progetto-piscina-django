import json

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .servizi.rilevamento_sdrai import rileva_sdrai_da_immagine
from .models import Piscina, Sdraio, DurataDisponibile, Prenotazione, DURATA_MINUTI


@staff_member_required
def elimina_sdraio(request, sdraio_id):
    if request.method != "POST":
        return JsonResponse({"errore": "Metodo non consentito"}, status=405)

    sdraio = get_object_or_404(Sdraio, id=sdraio_id)
    sdraio.delete()
    return JsonResponse({"ok": True})


@staff_member_required
def rigenera_sdrai(request, piscina_id):
    if request.method != "POST":
        return JsonResponse({"errore": "Metodo non consentito"}, status=405)

    piscina = get_object_or_404(Piscina, id=piscina_id)

    if not hasattr(piscina, "immagine") or not piscina.immagine.immagine:
        return JsonResponse({"errore": "Nessuna immagine associata"}, status=400)

    percorso_img = piscina.immagine.immagine.path

    # 🔥 Cancella TUTTI gli sdrai (anche manuali) - come nel tuo progetto attuale
    Sdraio.objects.filter(piscina=piscina).delete()

    sdrai_rilevati = rileva_sdrai_da_immagine(percorso_img, conf_min=0.30)

    for idx, s in enumerate(sdrai_rilevati, start=1):
        Sdraio.objects.create(
            piscina=piscina,
            x_percentuale=s.x_percentuale,
            y_percentuale=s.y_percentuale,
            origine="AI",
            etichetta=f"AI-{idx}"
        )

    return JsonResponse({"ok": True, "creati": len(sdrai_rilevati)})


@staff_member_required
@require_POST
def crea_sdraio(request, piscina_id):
    """
    Crea uno sdraio MANUALE (uno alla volta). Default 50%,50%.
    Accetta JSON opzionale: {x_percentuale, y_percentuale}
    """
    piscina = get_object_or_404(Piscina, id=piscina_id)

    x = 50.0
    y = 50.0
    try:
        if request.body:
            payload = json.loads(request.body.decode("utf-8"))
            if "x_percentuale" in payload:
                x = float(payload["x_percentuale"])
            if "y_percentuale" in payload:
                y = float(payload["y_percentuale"])
    except Exception:
        pass

    x = max(0.0, min(100.0, x))
    y = max(0.0, min(100.0, y))

    manuali_count = Sdraio.objects.filter(piscina=piscina, origine="MANUALE").count()
    etichetta = f"M-{manuali_count + 1:03d}"

    sdraio = Sdraio.objects.create(
        piscina=piscina,
        x_percentuale=x,
        y_percentuale=y,
        origine="MANUALE",
        etichetta=etichetta,
    )

    return JsonResponse({
        "ok": True,
        "id": sdraio.id,
        "x_percentuale": sdraio.x_percentuale,
        "y_percentuale": sdraio.y_percentuale,
        "origine": sdraio.origine,
        "etichetta": sdraio.etichetta,
    })


def home(request):
    piscina = Piscina.objects.filter(attiva=True).first() or Piscina.objects.last()

    sdrai = piscina.sdrai.all() if piscina else []
    durate = piscina.durate_disponibili.filter(attiva=True) if piscina else []

    is_staff = request.user.is_authenticated and request.user.is_staff

    return render(request, "pren/home.html", {
        "piscina": piscina,
        "sdrai": sdrai,
        "durate": durate,
        "can_drag": is_staff,
        "can_book": request.user.is_authenticated and not is_staff,
    })


@require_POST
def aggiorna_sdraio(request, sdraio_id):
    """
    Endpoint usato dal drag&drop:
    riceve JSON {x_percentuale, y_percentuale}
    salva e imposta origine="MANUALE"
    """
    sdraio = get_object_or_404(Sdraio, pk=sdraio_id)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errore": "JSON non valido"}, status=400)

    if "x_percentuale" not in payload or "y_percentuale" not in payload:
        return JsonResponse({"ok": False, "errore": "Campi mancanti"}, status=400)

    try:
        x = float(payload["x_percentuale"])
        y = float(payload["y_percentuale"])
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "errore": "Coordinate non valide"}, status=400)

    x = max(0.0, min(100.0, x))
    y = max(0.0, min(100.0, y))

    sdraio.x_percentuale = x
    sdraio.y_percentuale = y
    sdraio.origine = "MANUALE"
    sdraio.save(update_fields=["x_percentuale", "y_percentuale", "origine"])

    return JsonResponse({
        "ok": True,
        "id": sdraio.id,
        "x_percentuale": sdraio.x_percentuale,
        "y_percentuale": sdraio.y_percentuale,
        "origine": sdraio.origine,
    })


@require_GET
@login_required
def sdrai_occupati(request, piscina_id):
    """
    Ritorna lista ID sdrai occupati nell'intervallo selezionato.
    Query params:
      - inizio=YYYY-MM-DDTHH:MM
      - tipo_durata=...
    """
    piscina = get_object_or_404(Piscina, id=piscina_id)

    inizio_str = request.GET.get("inizio")
    tipo_durata = request.GET.get("tipo_durata")

    if not inizio_str or not tipo_durata:
        return JsonResponse({"errore": "Parametri mancanti"}, status=400)

    if not DurataDisponibile.objects.filter(piscina=piscina, tipo=tipo_durata, attiva=True).exists():
        return JsonResponse({"errore": "Durata non disponibile per questa piscina."}, status=400)

    try:
        inizio = timezone.datetime.fromisoformat(inizio_str)
    except Exception:
        return JsonResponse({"errore": "Formato data/ora non valido."}, status=400)

    if timezone.is_naive(inizio):
        inizio = timezone.make_aware(inizio)

    minuti = DURATA_MINUTI.get(tipo_durata)
    if minuti is None:
        return JsonResponse({"errore": "Tipo durata non valido."}, status=400)

    fine = inizio + timezone.timedelta(minutes=minuti)

    occupati = Prenotazione.objects.filter(
        piscina=piscina,
        inizio__lt=fine,
        fine__gt=inizio,
    ).values_list("sdraio_id", flat=True).distinct()

    return JsonResponse({"occupati": list(occupati)})


@login_required
def prenota_sdraio(request, sdraio_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "errore": "Metodo non consentito."}, status=405)

    piscina = Piscina.objects.filter(attiva=True).first() or Piscina.objects.last()
    if not piscina:
        return JsonResponse({"ok": False, "errore": "Nessuna piscina disponibile."}, status=400)

    sdraio = get_object_or_404(Sdraio, pk=sdraio_id, piscina=piscina)

    tipo_durata = request.POST.get("tipo_durata")
    inizio_str = request.POST.get("inizio")

    if not tipo_durata or not inizio_str:
        return JsonResponse({"ok": False, "errore": "Seleziona durata e data/ora di inizio."}, status=400)

    if not DurataDisponibile.objects.filter(piscina=piscina, tipo=tipo_durata, attiva=True).exists():
        return JsonResponse({"ok": False, "errore": "Durata non disponibile per questa piscina."}, status=400)

    try:
        inizio = timezone.datetime.fromisoformat(inizio_str)
    except Exception:
        return JsonResponse({"ok": False, "errore": "Formato data/ora non valido."}, status=400)

    if timezone.is_naive(inizio):
        inizio = timezone.make_aware(inizio)

    pren = Prenotazione(
        utente=request.user,
        piscina=piscina,
        sdraio=sdraio,
        tipo_durata=tipo_durata,
        inizio=inizio,
    )

    try:
        pren.save()
    except ValidationError as e:
        msg = "; ".join(e.messages) if hasattr(e, "messages") else str(e)

        if "già prenotato" in msg.lower():
            return JsonResponse({"ok": False, "errore": msg}, status=409)

        return JsonResponse({"ok": False, "errore": msg}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "errore": str(e)}, status=400)

    return JsonResponse({"ok": True})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "pren/signup.html", {"form": form})