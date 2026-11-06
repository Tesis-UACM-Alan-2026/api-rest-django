from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CategoriasViewSet

router = DefaultRouter()
router.register(r"categories", CategoriasViewSet, basename="categories")

urlpatterns = [
    path("", include(router.urls)),
]