from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class OptionalJWT(JWTAuthentication):
    """For public pages: a valid token identifies the member, but an expired or bad token is ignored
    (treated as a visitor) instead of breaking the page with a 401."""

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None
