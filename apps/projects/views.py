from django.views.generic import TemplateView
from django.shortcuts import render
from .models import Project


class HomeView(TemplateView):
    template_name = "projects/home.html"
