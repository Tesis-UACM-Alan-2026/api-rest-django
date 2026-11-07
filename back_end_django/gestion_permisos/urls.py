# gestion_permisos/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PermisosViewSet

# Crear un router y registrar el ViewSet
router = DefaultRouter()
router.register(r"permisos", PermisosViewSet, basename="permisos")
router.register(r"roles", RolesViewSet, basename="roles")

urlpatterns = [
    path('', include(router.urls)),
]