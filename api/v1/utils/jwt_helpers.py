import secrets


def generate_secret() -> str:
    secret = secrets.token_urlsafe(64)
    return secret
