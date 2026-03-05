"""
URL Configuration for operators app.
"""
from django.urls import path
from . import views

app_name = 'operators'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.OperatorDashboardView.as_view(), name='dashboard'),
    
    # List and CRUD
    path('', views.OperatorListView.as_view(), name='list'),
    path('<int:pk>/', views.OperatorDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.OperatorUpdateView.as_view(), name='update'),
    
    # Actions
    path('<int:pk>/verify/', views.OperatorVerifyView.as_view(), name='verify'),
    path('<int:pk>/sync-odoo/', views.OperatorSyncOdooView.as_view(), name='sync_odoo'),
]