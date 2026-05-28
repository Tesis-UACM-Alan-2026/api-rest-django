from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

def create_authenticated_client(user=None):
    if not user:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, user