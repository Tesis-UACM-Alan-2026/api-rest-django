from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from autentificacion.views import (
    CustomTokenObtainPairView,
    LogoutView,
)
from autentificacion.log_views import (
    LogAuditoriaView,
    LogTecnicoView,
)

urlpatterns = [
    path(
        'token/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'logout/',
        LogoutView.as_view(),
        name='logout'
    ),
    path(
        'logs/auditoria/',
        LogAuditoriaView.as_view(),
        name='log_auditoria'
    ),
    path(
        'logs/tecnico/',
        LogTecnicoView.as_view(),
        name='log_tecnico'
    ),
]