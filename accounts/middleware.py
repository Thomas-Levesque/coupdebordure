# accounts/middleware.py
from django.utils import translation

class ProfileLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            lang = getattr(getattr(user, "profile", None), "language", "") or ""
            if lang:
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response