import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .servizi.rilevamento_sdrai import rileva_sdrai_da_immagine
from .models import Piscina, Sdraio, DurataDisponibile, Prenotazione


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

    # 🔥 Cancella TUTTI gli sdrai (anche manuali)
    Sdraio.objects.filter(piscina=piscina).delete()

    # Rilevamento
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

def home(request):
    # Piscina attiva (fallback: ultima)
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

    # clamp opzionale (evita valori strani)
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


@login_required
def prenota_sdraio(request, sdraio_id):
    """
    Prenotazione: l'utente sceglie
    - tipo_durata (una delle DurataDisponibile attive per la piscina)
    - inizio (datetime-local)
    e clicca su uno sdraio.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo non consentito.")

    piscina = Piscina.objects.filter(attiva=True).first() or Piscina.objects.last()
    if not piscina:
        return HttpResponseBadRequest("Nessuna piscina disponibile.")

    # lo sdraio deve appartenere alla piscina corrente
    sdraio = get_object_or_404(Sdraio, pk=sdraio_id, piscina=piscina)

    tipo_durata = request.POST.get("tipo_durata")
    inizio_str = request.POST.get("inizio")

    if not tipo_durata or not inizio_str:
        return HttpResponseBadRequest("Seleziona durata e data/ora di inizio.")

    # durata deve essere attiva per questa piscina
    if not DurataDisponibile.objects.filter(piscina=piscina, tipo=tipo_durata, attiva=True).exists():
        return HttpResponseBadRequest("Durata non disponibile per questa piscina.")

    # datetime-local arriva come "YYYY-MM-DDTHH:MM"
    try:
        inizio = timezone.datetime.fromisoformat(inizio_str)
    except Exception:
        return HttpResponseBadRequest("Formato data/ora non valido.")

    # rendi timezone-aware se necessario
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
        # qui clean() blocca sovrapposizioni
        pren.save()
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    return redirect("home")




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
