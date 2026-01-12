from django.shortcuts import render
from django.utils.translation import get_language

def home_view(request):
    return render(request, "pages/home.html")

def offline_view(request):
    return render(request, "pages/offline.html")

def cgu_view(request):
    lang = (get_language() or "fr")[:2]
    return render(request, f"legal/cgu_{lang}.html")


def privacy_view(request):
    lang = (get_language() or "fr")[:2]
    return render(request, f"legal/privacy_{lang}.html")


def mentions_legales_view(request):
    lang = (get_language() or "fr")[:2]
    return render(request, f"legal/mentions_legales_{lang}.html")