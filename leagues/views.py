from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LeagueCreateForm, LeagueJoinForm
from .models import League, LeagueMember

from .models import League, LeagueMember, LeagueMessage
from .forms import LeagueMessageForm

from races.models import Season

@login_required
def leagues_home(request):
    my_leagues = League.objects.filter(memberships__user=request.user).distinct().order_by("name")
    owned = League.objects.filter(owner=request.user).order_by("name")
    return render(request, "leagues/leagues_home.html", {"my_leagues": my_leagues, "owned": owned})

@login_required
def league_create(request):
    if request.method == "POST":
        form = LeagueCreateForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.owner = request.user
            league.save()
            LeagueMember.objects.get_or_create(league=league, user=request.user)
            messages.success(request, "Ligue créée ✅")
            return redirect("leagues_home")
    else:
        form = LeagueCreateForm()
    return render(request, "leagues/league_create.html", {"form": form})

@login_required
def league_join(request):
    if request.method == "POST":
        form = LeagueJoinForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["invite_code"].strip().upper()
            league = get_object_or_404(League, invite_code=code)
            try:
                LeagueMember.objects.create(league=league, user=request.user)
                messages.success(request, f"Tu as rejoint la ligue “{league.name}” ✅")
            except IntegrityError:
                messages.info(request, "Tu es déjà membre de cette ligue.")
            return redirect("leagues_home")
    else:
        form = LeagueJoinForm()
    return render(request, "leagues/league_join.html", {"form": form})

@login_required
def league_detail(request, league_id):
    league = get_object_or_404(League, id=league_id)

    is_member = LeagueMember.objects.filter(league=league, user=request.user).exists()
    if not is_member:
        messages.error(request, "Accès refusé : tu n’es pas membre de cette ligue.")
        return redirect("leagues_home")

    members = (
        LeagueMember.objects
        .filter(league=league)
        .select_related("user")
        .order_by("joined_at")
    )

    seasons = Season.objects.all().order_by("-year")

    return render(request, "leagues/league_detail.html", {
        "league": league,
        "members": members,
        "seasons": seasons,
    })


@login_required
def league_detail(request, league_id):
    league = get_object_or_404(League, id=league_id)

    is_member = LeagueMember.objects.filter(league=league, user=request.user).exists()
    if not is_member:
        messages.error(request, "Accès refusé : tu n’es pas membre de cette ligue.")
        return redirect("leagues_home")

    members = (LeagueMember.objects
               .filter(league=league)
               .select_related("user")
               .order_by("joined_at"))

    seasons = Season.objects.all().order_by("-year")

    # --- Conversation (POST) ---
    if request.method == "POST":
        form = LeagueMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.league = league
            msg.author = request.user
            msg.save()
            return redirect("league_detail", league_id=league.id)
    else:
        form = LeagueMessageForm()

    # --- Pagination messages (GET) ---
    qs = (LeagueMessage.objects
          .filter(league=league)
          .select_related("author", "author__profile")  # si profile existe
          .order_by("-created_at"))

    paginator = Paginator(qs, 30)
    page_number = request.GET.get("page")  # ?page=2
    page_obj = paginator.get_page(page_number)  # robuste

    return render(request, "leagues/league_detail.html", {
        "league": league,
        "members": members,
        "seasons": seasons,
        "form": form,
        "page_obj": page_obj,   # messages paginés
    })