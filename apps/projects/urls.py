from django.urls import path

from .views import HomeView


app_name = "projects"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]

