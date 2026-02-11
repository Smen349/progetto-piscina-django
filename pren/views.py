from django.shortcuts import render, get_object_or_404
from .models import Piscina, Sdraio
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


def home(request):
    piscina = Piscina.objects.first()
    sdrai = piscina.sdrai.all() if piscina else []
    return render(request, "pren/home.html", {
        "piscina": piscina,
        "sdrai": sdrai,
        })


@require_POST
def aggiorna_sdraio(request, sdraio_id):
    try:
        data = json.loads(request.body.decode("utf-8"))
        x = data.get("x_percentuale")
        y = data.get("y_percentuale")

        if x is None or y is None:

            return JsonResponse(
                {"ok": False, "errore": "x_percentuale e y_percentuale sono obbligatori"},
                status=400
            )

        try:
            x = float(x)
            y = float(y)
        except (TypeError, ValueError):
            return JsonResponse(
                {"ok": False, "errore": "x_percentuale e y_percentuale devono essere numeri"},
                status=400
            )
        
        sdraio = get_object_or_404(Sdraio, pk=sdraio_id)

        sdraio.x_percentuale = x
        sdraio.y_percentuale = y
        sdraio.origine = "MANUALE"
        sdraio.save()

    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errore": "JSON non valido"}, status=400)
    
    return JsonResponse({
        "ok": True, 
        "id": sdraio.id,
        "x_percentuale": sdraio.x_percentuale,
        "y_percentuale": sdraio.y_percentuale,
        "origine": sdraio.origine,
        })
