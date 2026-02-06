from django.shortcuts import render
from .models import Piscina

def home(request):
    piscina = Piscina.objects.first()
    sdrai = piscina.sdrai.all() if piscina else []
    return render(request, "pren/home.html", {
        "piscina": piscina,
        "sdrai": sdrai,
        })


