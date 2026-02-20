"""
Views for operators app.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q, Count
from django_htmx.http import HttpResponseClientRedirect
import logging

from .models import Operator
from .services import OperatorService

logger = logging.getLogger(__name__)


class OperatorDashboardView(LoginRequiredMixin, DetailView):
    """Dashboard view for Operator statistics and quick actions."""
    template_name = 'operators/operator_dashboard.html'
    
    def get_object(self):
        """Return None (not used, but required by DetailView)."""
        return None
    
    def get_context_data(self, **kwargs):
        """Add operator statistics and alerts."""
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        stats = OperatorService.get_operator_statistics()
        context['stats'] = stats
        
        # Get unverified operators (need attention)
        context['unverified_operators'] = OperatorService.get_unverified_operators()[:10]
        
        # Get operators not synced to Odoo
        context['not_synced_operators'] = OperatorService.get_operators_not_synced_to_odoo()[:10]
        
        # Get active operators count
        context['active_count'] = stats.get('by_status', {}).get('active', 0)
        # Prepare percentage breakdowns for templates (avoid template math)
        total = stats.get('total') or 0
        by_type = stats.get('by_type', {}) or {}
        by_status = stats.get('by_status', {}) or {}

        stats_by_type_list = []
        for k, v in by_type.items():
            pct = round((v / total * 100), 0) if total > 0 else 0
            stats_by_type_list.append({'key': k, 'count': v, 'pct': pct})

        stats_by_status_list = []
        for k, v in by_status.items():
            pct = round((v / total * 100), 0) if total > 0 else 0
            stats_by_status_list.append({'key': k, 'count': v, 'pct': pct})

        context['stats_by_type_list'] = stats_by_type_list
        context['stats_by_status_list'] = stats_by_status_list
        
        return context


class OperatorListView(LoginRequiredMixin, ListView):
    """List view for Operators."""
    model = Operator
    template_name = 'operators/operator_list.html'
    context_object_name = 'operators'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter operators based on query parameters."""
        queryset = Operator.objects.select_related('created_by').all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type
        operator_type = self.request.GET.get('type')
        if operator_type:
            queryset = queryset.filter(type=operator_type)
        
        # Filter by verification
        is_verified = self.request.GET.get('is_verified')
        if is_verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif is_verified == 'false':
            queryset = queryset.filter(is_verified=False)
        
        # Filter by Odoo sync
        odoo_synced = self.request.GET.get('odoo_synced')
        if odoo_synced == 'true':
            queryset = queryset.filter(odoo_partner_id__isnull=False)
        elif odoo_synced == 'false':
            queryset = queryset.filter(odoo_partner_id__isnull=True)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(legal_name__icontains=search) |
                Q(email__icontains=search) |
                Q(city__icontains=search) |
                Q(gg_operator_id__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        
        # Add filter choices
        context['statuses'] = Operator.Status.choices
        context['types'] = Operator.Type.choices
        
        # Add current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_is_verified'] = self.request.GET.get('is_verified', '')
        context['current_odoo_synced'] = self.request.GET.get('odoo_synced', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        # Add statistics
        context['stats'] = OperatorService.get_operator_statistics()
        
        return context


class OperatorDetailView(LoginRequiredMixin, DetailView):
    """Detail view for Operator."""
    model = Operator
    template_name = 'operators/operator_detail.html'
    context_object_name = 'operator'
    
    def get_queryset(self):
        return Operator.objects.select_related('created_by').prefetch_related('projects')
    
    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        
        # Get operator's projects
        context['projects'] = self.object.projects.all().order_by('-created_at')
        
        # Get audit history
        from apps.audits.services import AuditLogService
        context['audit_history'] = AuditLogService.get_object_history(
            'Operator',
            str(self.object.id),
            limit=10
        )
        
        return context


class OperatorUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for Operator."""
    model = Operator
    template_name = 'operators/operator_form.html'
    fields = [
        'name', 'legal_name', 'acronym', 'type', 'status',
        'email', 'phone', 'website',
        'address', 'city', 'postal_code', 'country',
        'registration_number', 'tax_id',
        'contact_person', 'contact_email', 'contact_phone',
        'notes'
    ]
    
    def get_success_url(self):
        return reverse_lazy('operators:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Update operator with service."""
        data = {k: v for k, v in form.cleaned_data.items() if k in form.changed_data}
        
        try:
            operator = OperatorService.update_operator(
                operator=self.object,
                data=data,
                user=self.request.user,
                request=self.request
            )
            
            messages.success(
                self.request,
                f'Opérateur "{operator.name}" mis à jour avec succès.'
            )
            
            return redirect('operators:detail', pk=operator.pk)
            
        except Exception as e:
            logger.error(f"Error updating operator: {e}")
            messages.error(
                self.request,
                f'Erreur lors de la mise à jour: {str(e)}'
            )
            return self.form_invalid(form)


class OperatorVerifyView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Verify an operator."""
    model = Operator
    permission_required = 'operators.change_operator'
    
    def post(self, request, *args, **kwargs):
        """Handle verification."""
        operator = self.get_object()
        
        # Check permission
        if not request.user.has_perm('operators.change_operator'):
            messages.error(request, "Vous n'avez pas la permission de vérifier les opérateurs.")
            return redirect('operators:detail', pk=operator.pk)
        
        try:
            OperatorService.verify_operator(
                operator=operator,
                user=request.user,
                request=request
            )
            
            messages.success(
                request,
                f'Opérateur "{operator.name}" vérifié avec succès.'
            )
            
            # Return HTMX redirect if HTMX request
            if request.headers.get('HX-Request'):
                return HttpResponseClientRedirect(reverse_lazy('operators:detail', kwargs={'pk': operator.pk}))
            
        except Exception as e:
            logger.error(f"Error verifying operator: {e}", exc_info=True)
            messages.error(
                request,
                f'Erreur lors de la vérification: {str(e)}'
            )
        
        return redirect('operators:detail', pk=operator.pk)


class OperatorSyncOdooView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Sync operator to Odoo."""
    model = Operator
    permission_required = 'operators.change_operator'
    
    def post(self, request, *args, **kwargs):
        """Handle Odoo sync."""
        operator = self.get_object()
        
        # Check permission
        if not request.user.has_perm('operators.change_operator'):
            messages.error(request, "Vous n'avez pas la permission de synchroniser vers Odoo.")
            return redirect('operators:detail', pk=operator.pk)
        
        try:
            partner_id = OperatorService.sync_to_odoo(
                operator=operator,
                user=request.user
            )
            
            messages.success(
                request,
                f'Opérateur "{operator.name}" synchronisé vers Odoo (Partner ID: {partner_id}).'
            )
            
            # Return HTMX redirect if HTMX request
            if request.headers.get('HX-Request'):
                return HttpResponseClientRedirect(reverse_lazy('operators:detail', kwargs={'pk': operator.pk}))
            
        except Exception as e:
            logger.error(f"Error syncing to Odoo: {e}", exc_info=True)
            messages.error(
                request,
                f'Erreur lors de la synchronisation vers Odoo: {str(e)}'
            )
        
        return redirect('operators:detail', pk=operator.pk)