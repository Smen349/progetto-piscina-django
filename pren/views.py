from django.shortcuts import render
from .models import Piscina

def home(request):
    piscina = Piscina.objects.first()
    return render(request, "pren/home.html", {"piscina": piscina})


