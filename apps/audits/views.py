"""
Views for audits app.
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import logging

from .models import IntegrationEvent, AuditLog
from .services import IntegrationEventService

logger = logging.getLogger(__name__)


class IntegrationEventListView(LoginRequiredMixin, ListView):
    """List view for Integration Events."""
    model = IntegrationEvent
    template_name = 'audits/integration_event_list.html'
    context_object_name = 'events'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter events based on query parameters."""
        queryset = IntegrationEvent.objects.select_related('created_by').all()
        
        # Filtrer par système
        system = self.request.GET.get('system')
        if system:
            queryset = queryset.filter(system=system)
        
        # Filtrer par direction
        direction = self.request.GET.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)
        
        # Filtrer par status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(external_id__icontains=search) |
                Q(error_message__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        
        # Add filter choices
        context['systems'] = IntegrationEvent.System.choices
        context['directions'] = IntegrationEvent.Direction.choices
        context['statuses'] = IntegrationEvent.Status.choices
        
        # Add current filters
        context['current_system'] = self.request.GET.get('system', '')
        context['current_direction'] = self.request.GET.get('direction', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        # Add statistics
        last_24h = timezone.now() - timedelta(hours=24)
        context['stats'] = IntegrationEventService.get_statistics(start_date=last_24h)
        
        return context


class IntegrationEventDetailView(LoginRequiredMixin, DetailView):
    """Detail view for Integration Event."""
    model = IntegrationEvent
    template_name = 'audits/integration_event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return IntegrationEvent.objects.select_related('created_by')


class AuditLogListView(LoginRequiredMixin, ListView):
    """List view for Audit Logs."""
    model = AuditLog
    template_name = 'audits/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter logs based on query parameters."""
        queryset = AuditLog.objects.select_related('user').all()
        
        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by model
        model_name = self.request.GET.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by user
        user_id = self.request.GET.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(object_id__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        
        # Add filter choices
        context['actions'] = AuditLog.Action.choices
        
        # Get unique model names
        context['model_names'] = (
            AuditLog.objects.values_list('model_name', flat=True)
            .distinct()
            .order_by('model_name')
        )
        
        # Add current filters
        context['current_action'] = self.request.GET.get('action', '')
        context['current_model_name'] = self.request.GET.get('model_name', '')
        context['current_user_id'] = self.request.GET.get('user_id', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """Detail view for Audit Log."""
    model = AuditLog
    template_name = 'audits/audit_log_detail.html'
    context_object_name = 'log'
    
    def get_queryset(self):
        return AuditLog.objects.select_related('user')


class DashboardView(LoginRequiredMixin, ListView):
    """Dashboard view with statistics and recent events."""
    template_name = 'audits/Dashboard.html'
    model = IntegrationEvent
    context_object_name = 'recent_events'
    paginate_by = 10

    def get_queryset(self):
        """Get recent integration events."""
        return IntegrationEvent.objects.select_related('created_by').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add dashboard statistics."""
        context = super().get_context_data(**kwargs)
        
        # Statistics for different time periods
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        context['stats_24h'] = IntegrationEventService.get_statistics(start_date=last_24h)
        context['stats_7d'] = IntegrationEventService.get_statistics(start_date=last_7d)
        context['stats_30d'] = IntegrationEventService.get_statistics(start_date=last_30d)
        
        # Failed events that need attention
        context['failed_events'] = IntegrationEventService.get_failed_events()[:10]
        
        # Recent audit logs
        context['recent_logs'] = AuditLog.objects.select_related('user')[:10]
        
        # Activity by system
        context['events_by_system'] = (
            IntegrationEvent.objects
            .filter(created_at__gte=last_7d)
            .values('system')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Activity by status
        context['events_by_status'] = (
            IntegrationEvent.objects
            .filter(created_at__gte=last_7d)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        return context