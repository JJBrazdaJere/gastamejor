from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("producto/<int:pk>/", views.detalle, name="detalle"),
]
