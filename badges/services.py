# badges/services.py

from __future__ import annotations

from typing import Dict, Set, Tuple

from django.db import transaction
from django.db.models import Q, Sum

from badges.models import Badge, UserBadge
from bets.models import BetScore, Bet
from races.models import OneDayRace, Stage, Tour


MONUMENTS = {
    "Milan-San Remo",
    "Tour des Flandres",
    "Paris-Roubaix",
    "Liège-Bastogne-Liège",
    "Tour de Lombardie",
}

GRAND_TOURS = {
    "Tour de France",
    "Tour d'Italie",
    "Tour d'Espagne",
}


# -------------------------
# Helpers / Attribution
# -------------------------

def user_id_to_user(user_id):
    # import local pour éviter imports circulaires
    from accounts.models import User
    return User.objects.get(id=user_id)


from django.db import IntegrityError, transaction

def award_badge(user, badge_code: str, context: dict | None = None) -> bool:
    """
    Attribue un badge si Badge(code=badge_code) existe.
    Ne plante jamais si le badge est déjà attribué (contrainte uniq_user_badge).
    """
    context = context or {}
    badge = Badge.objects.filter(code=badge_code).first()
    if not badge:
        return False

    try:
        with transaction.atomic():
            ub, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={"context": context},
            )
    except IntegrityError:
        # sécurité si deux process tentent en même temps
        return False

    # Optionnel : si tu veux mettre à jour le context quand le badge existe déjà
    # (ex: WIN_UNIT sur une autre course / étape)
    if not created and context and ub.context != context:
        ub.context = context
        ub.save(update_fields=["context"])

    return created


def award_first_bet(user) -> bool:
    """
    Badge "premier prono" : quand l'utilisateur a exactement 1 Bet en base.
    (appelé juste après la sauvegarde du prono)
    """
    if Bet.objects.filter(user=user).count() == 1:
        return award_badge(user, "FIRST_BET", {"type": "global"})
    return False


# -------------------------
# Badges liés aux résultats
# -------------------------

def update_unit_winner_badge(one_day_race: OneDayRace | None = None, stage: Stage | None = None):
    """
    Attribue le badge WIN_UNIT au meilleur score sur une course/étape.
    Tie-break : submitted_at.
    """
    if (one_day_race is None and stage is None) or (one_day_race is not None and stage is not None):
        # sécurité : exactement 1 des 2
        return

    if one_day_race:
        qs = BetScore.objects.filter(bet__one_day_race=one_day_race)
        ctx = {"type": "one_day", "id": one_day_race.id}
    else:
        qs = BetScore.objects.filter(bet__stage=stage)
        ctx = {"type": "stage", "id": stage.id}

    best = (
        qs.select_related("bet__user", "bet")
          .order_by("-score", "bet__submitted_at")
          .first()
    )
    if not best:
        return

    award_badge(best.bet.user, "WIN_UNIT", ctx)


def update_tour_badges(tour: Tour):
    """
    Badges tour basés sur le classement (somme des scores des étapes).
    WIN_TOUR pour le 1er + RED_LANTERN_TOUR pour le dernier.
    """
    rows = list(
        BetScore.objects
        .filter(bet__stage__tour=tour)
        .values("bet__user_id", "bet__user__username")
        .annotate(total=Sum("score"))
        .order_by("-total", "bet__user__username")
    )
    if not rows:
        return

    winner_user_id = rows[0]["bet__user_id"]
    last_user_id = rows[-1]["bet__user_id"]

    context = {"type": "tour", "id": tour.id}
    award_badge(user_id_to_user(winner_user_id), "WIN_TOUR", context)
    award_badge(user_id_to_user(last_user_id), "RED_LANTERN_TOUR", context)

    # Optionnel : tente aussi le badge "saison complète" pour le vainqueur
    award_season_full(user_id_to_user(winner_user_id), tour.season)


def award_season_full(user, season) -> bool:
    """
    Exemple historique (ancien) : toutes les unités jouées (one_day + toutes étapes).
    Attention: ici "joué" = Bet existant, pas forcément Top5 complet.
    """
    total_units = (
        OneDayRace.objects.filter(season=season).count()
        + Stage.objects.filter(tour__season=season).count()
    )

    user_units = (
        Bet.objects.filter(user=user, one_day_race__season=season).count()
        + Bet.objects.filter(user=user, stage__tour__season=season).count()
    )

    if total_units > 0 and user_units >= total_units:
        return award_badge(user, "SEASON_FULL", {"season": season.year})
    return False


# -------------------------
# Badges "participation saison" (Option 1 + monuments + GT)
# -------------------------

def _picks_ok_q():
    """Top5 complet = pick1..pick5 non nuls + submitted_at non nul."""
    return (
        Q(submitted_at__isnull=False)
        & Q(pick1__isnull=False)
        & Q(pick2__isnull=False)
        & Q(pick3__isnull=False)
        & Q(pick4__isnull=False)
        & Q(pick5__isnull=False)
    )


def _season_participation_sets(user, year: int) -> Tuple[Set[int], Set[int]]:
    """
    Retourne :
    - ids one_day joués (Top5 validé)
    - ids stage joués (Top5 validé)
    """
    bets = (
        Bet.objects.filter(user=user)
        .filter(_picks_ok_q())
        .filter(Q(one_day_race__season__year=year) | Q(stage__tour__season__year=year))
        .values_list("one_day_race_id", "stage_id")
    )

    one_day_ids: Set[int] = set()
    stage_ids: Set[int] = set()
    for od_id, st_id in bets:
        if od_id:
            one_day_ids.add(od_id)
        if st_id:
            stage_ids.add(st_id)

    return one_day_ids, stage_ids


@transaction.atomic
def evaluate_user_badges_for_season(user, year: int):
    """
    À appeler après bet.save().

    - FIRST_UNIT_PLAYED_{year} : au moins 1 course/étape jouée sur l'année (Option 1)
    - SEASON_FINISHER_{year}   : toutes les one-day + pour chaque tour au moins 1 étape jouée
    - MONUMENT_FINISHER_{year} : participation aux 5 monuments (one-day)
    - GRANDTOUR_FINISHER_{year}: participation à au moins 1 étape de chacun des 3 grands tours
    """
    participated_one_days, participated_stages = _season_participation_sets(user, year)

    # Option 1 : au moins une unité jouée
    if participated_one_days or participated_stages:
        award_badge(user, f"FIRST_UNIT_PLAYED_{year}", {"year": year})

    # Saison complète : toutes les one-day + au moins 1 étape par tour
    one_days_all = set(OneDayRace.objects.filter(season__year=year).values_list("id", flat=True))
    one_day_ok = bool(one_days_all) and one_days_all.issubset(participated_one_days)

    tours = list(Tour.objects.filter(season__year=year).values_list("id", flat=True))
    tours_ok = True
    if tours:
        stages_by_tour: Dict[int, Set[int]] = {}
        for tour_id, stage_id in Stage.objects.filter(tour_id__in=tours).values_list("tour_id", "id"):
            stages_by_tour.setdefault(tour_id, set()).add(stage_id)

        for tour_id in tours:
            stage_ids = stages_by_tour.get(tour_id, set())
            if not stage_ids:
                tours_ok = False
                break
            if stage_ids.isdisjoint(participated_stages):
                tours_ok = False
                break
    else:
        tours_ok = False

    if one_day_ok and tours_ok:
        award_badge(user, f"SEASON_FINISHER_{year}", {"year": year})

    # Monuments
    monuments_ids = set(
        OneDayRace.objects.filter(season__year=year, name__in=MONUMENTS).values_list("id", flat=True)
    )
    if len(monuments_ids) == 5 and monuments_ids.issubset(participated_one_days):
        award_badge(user, f"MONUMENT_FINISHER_{year}", {"year": year})

    # Grands Tours
    gt_ids = list(Tour.objects.filter(season__year=year, name__in=GRAND_TOURS).values_list("id", flat=True))
    gt_ok = (len(gt_ids) == 3)
    if gt_ok:
        stages_by_gt: Dict[int, Set[int]] = {}
        for tour_id, stage_id in Stage.objects.filter(tour_id__in=gt_ids).values_list("tour_id", "id"):
            stages_by_gt.setdefault(tour_id, set()).add(stage_id)

        for tour_id in gt_ids:
            stage_ids = stages_by_gt.get(tour_id, set())
            if not stage_ids or stage_ids.isdisjoint(participated_stages):
                gt_ok = False
                break

    if gt_ok:
        award_badge(user, f"GRANDTOUR_FINISHER_{year}", {"year": year})