def cookie_consent(request):
    ads_allowed = request.COOKIES.get("cdb_ads") == "true"
    analytics_allowed = request.COOKIES.get("cdb_analytics") == "true"
    return {
        "ads_allowed": ads_allowed,
        "analytics_allowed": analytics_allowed,
    }