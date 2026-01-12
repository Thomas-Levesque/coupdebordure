from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup_view, dashboard_view
from .views_account import account_view
from .views import verify_email_view
from .views import set_language_pro

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("account/", account_view, name="account"),
    path("verify-email/<uidb64>/<token>/", verify_email_view, name="verify_email"),
    path("set-language-pro/", set_language_pro, name="set_language_pro"),
]
