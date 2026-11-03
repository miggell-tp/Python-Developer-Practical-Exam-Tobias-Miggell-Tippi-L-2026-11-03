from django.urls import path

from .views import CarCreateView, CarDeleteView, CarListView, CarUpdateView


app_name = "cars"

urlpatterns = [
    path("", CarListView.as_view(), name="list"),
    path("add/", CarCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", CarUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", CarDeleteView.as_view(), name="delete"),
]