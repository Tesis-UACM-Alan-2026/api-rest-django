"""
Configuración de URL para el proyecto HIMFG.

Esta configuración define las rutas principales del proyecto, incluyendo:
- Panel de administración.
- Documentación Swagger y Redoc de la API.
- Endpoints de la app 'user'.

Para más información, consulta:
https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from user.views.auth_users import PublicKeyView
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.shortcuts import redirect
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from user.views.auth_users import CustomTokenObtainPairView, CustomTokenRefreshView, CustomTokenVerifyView

# from user.views import prueba_log  # Vista de prueba (comentada por ahora)

# Configuración del esquema OpenAPI para la documentación interactiva
schema_view = get_schema_view(
    openapi.Info(
        title="API de HIMFG",
        default_version='v1',
        description="API para la documentación y acceso a los servicios del proyecto HIMFG.",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="luis.quiroz@uacm.edu.mx"),
        license=openapi.License(name="Awesome License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),  # Permitir acceso público a la documentación
)

# Lista de rutas disponibles en el proyecto
urlpatterns = [
    path('', lambda request: redirect('schema-swagger-ui', permanent=False)),  # Redirección raíz
    path('api/auth/login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify', CustomTokenVerifyView.as_view(), name='token_verify'),
    path("api/auth/public-key/", PublicKeyView.as_view(), name="public-key"),
    path('admin/', admin.site.urls),  # Ruta del panel de administración de Django
    # path('prueba-log/', prueba_log, name='prueba_log'),  # Ruta de prueba comentada
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # UI Swagger
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # UI Redoc
    path('api/users/', include('user.urls')),  # Rutas de la app de usuarios

]
