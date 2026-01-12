# bets/leaderboards_utils.py
from __future__ import annotations

from typing import Dict, List, Set

from django.templatetags.static import static

from accounts.models import Profile


def _flag_url_from_country(country: str | None) -> str:
    """
    Drapeaux en statique : static/flags/fr.svg, static/flags/be.svg, etc.
    Fallback : static/flags/_unknown.svg
    """
    if not country:
        return static("flags/_unknown.svg")

    c = country.strip().lower()
    if len(c) != 2:
        return static("flags/_unknown.svg")

    # NB: on suppose que tes fichiers sont en minuscules (fr.svg, be.svg, ...)
    return static(f"flags/{c}.svg")


def _badge_icon_url_from_profile(p: Profile | None) -> str:
    """
    Badge affiché :
    - si Badge.icon (upload) existe => badge.icon.url
    - sinon fallback static/ (static/badges/<code>.svg)
    - sinon fallback static/badges/_unknown.svg
    """
    if not p or not p.featured_badge_id or not p.featured_badge:
        return ""

    badge = p.featured_badge

    # 1) upload via ImageField/FileField
    icon = getattr(badge, "icon", None)
    if icon:
        try:
            return icon.url
        except Exception:
            pass

    # 2) fallback statique basé sur le code
    code = (badge.code or "").strip().lower()
    if code:
        return static(f"badges/{code}.svg")

    return static("badges/_unknown.svg")


def finalize_rows(rows_full: List[Dict], request_user_id: int) -> None:
    for idx, r in enumerate(rows_full, start=1):
        r["rank"] = idx
        r["is_me"] = (r["user_id"] == request_user_id)


def enrich_rows_with_profile(rows_full: List[Dict]) -> None:
    """
    Ajoute à chaque ligne :
      - avatar_url
      - badge_icon_url (avec fallback)
      - country (ISO2)
      - flag_url (avec fallback)
    """
    user_ids = [r["user_id"] for r in rows_full]

    profiles = {
        p.user_id: p
        for p in Profile.objects.filter(user_id__in=user_ids).select_related("featured_badge")
    }

    for r in rows_full:
        p = profiles.get(r["user_id"])

        r["avatar_url"] = p.avatar_url if p else ""
        country = (str(p.country) or "").strip() if p else ""
        r["country"] = country

        r["flag_url"] = _flag_url_from_country(country)
        r["badge_icon_url"] = _badge_icon_url_from_profile(p)


def build_compact_rows(
    rows_full: List[Dict],
    *,
    request_user_id: int,
    top_n: int = 5,
    bottom_n: int = 3,
    around_user: int = 1,
) -> List[Dict]:
    n = len(rows_full)
    if n <= top_n + bottom_n + (2 * around_user + 1):
        return rows_full

    user_idx = next((i for i, r in enumerate(rows_full) if r["user_id"] == request_user_id), None)

    keep: Set[int] = set(range(0, min(top_n, n)))
    keep |= set(range(max(n - bottom_n, 0), n))

    if user_idx is not None:
        start = max(user_idx - around_user, 0)
        end = min(user_idx + around_user, n - 1)
        keep |= set(range(start, end + 1))

    out: List[Dict] = []
    last = None
    for i in range(n):
        if i in keep:
            if last is not None and i > last + 1:
                out.append({"ellipsis": True})
            out.append(rows_full[i])
            last = i
    return out