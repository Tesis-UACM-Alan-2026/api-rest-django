# conftest.py

import pytest


@pytest.fixture(autouse=True)
def hasher_rapido_en_tests(settings):
    """
    Las contraseñas de prueba no necesitan un hasheo costoso: con MD5 la suite
    corre mucho más rápido. Solo afecta a los tests, nunca a producción.
    """
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]