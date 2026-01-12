from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("", include("accounts.urls")),
    path("", include("races.urls")),
    path("", include("bets.urls")),
    path("", include("leagues.urls")),
    path("push/", include("pushes.urls")),
    path("", include("stats.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("i18n/set-language-pro/", accounts_views.set_language_pro, name="set_language_pro"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)