"""
URL Configuration for audits app.
"""
from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Integration Events
    path('events/', views.IntegrationEventListView.as_view(), name='event_list'),
    path('events/<int:pk>/', views.IntegrationEventDetailView.as_view(), name='event_detail'),
    
    # Audit Logs
    path('logs/', views.AuditLogListView.as_view(), name='log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
]