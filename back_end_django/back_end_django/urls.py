#############CODIGO 7############################
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="APIrest",
        default_version="v4",
        description="Documentación de la API",
        terms_of_service="https://www.tusitio.com/terms/",
        contact=openapi.Contact(email="soporte@tusitio.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/usuarios/", include("gestion_usuarios.urls")),  # <-- esta línea es la clave
    path("api/productos/", include("gestion_productos.urls")), #Nuevo PRACTICA5
    path("api/auth/", include("autentificacion.urls")), #Nuevo PRACTICA6 #tambien se mejoraron para usuarioos y productos
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]