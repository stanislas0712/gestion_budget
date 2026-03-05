"""
Business logic services for audits app.
Gestion des événements d'audit et de traçabilité.
"""
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
import logging
import traceback
import time

from .models import IntegrationEvent, AuditLog

logger = logging.getLogger(__name__)


class IntegrationEventService:
    """Service for managing integration events."""
    
    @staticmethod
    @transaction.atomic
    def create_event(
        event_type: str,
        source_system: str,
        destination_system: str = '',
        external_id: str = '',
        internal_id: str = '',
        request_data: Optional[Dict] = None,
        user: Optional[User] = None
    ) -> IntegrationEvent:
        """
        Create a new integration event.
        
        Args:
            event_type: Type of event (from IntegrationEvent.EventType)
            source_system: Source system name (goodgrants, django, odoo)
            destination_system: Destination system name
            external_id: ID in external system
            internal_id: ID in Django
            request_data: Request payload
            user: User who triggered the event
            
        Returns:
            IntegrationEvent instance
        """
        event = IntegrationEvent.objects.create(
            event_type=event_type,
            source_system=source_system,
            destination_system=destination_system,
            external_id=external_id,
            internal_id=internal_id,
            request_data=request_data or {},
            created_by=user,
            status=IntegrationEvent.Status.PENDING
        )
        
        logger.info(
            f"Created integration event {event.id}: "
            f"{event.event_type} ({source_system} -> {destination_system})"
        )
        
        return event
    
    @staticmethod
    @transaction.atomic
    def mark_success(
        event: IntegrationEvent,
        response_data: Optional[Dict] = None,
        duration_ms: Optional[int] = None
    ) -> IntegrationEvent:
        """Mark an event as successful."""
        event.mark_success(response_data, duration_ms)
        
        logger.info(
            f"Event {event.id} marked as success "
            f"(duration: {duration_ms}ms)" if duration_ms else ""
        )
        
        return event
    
    @staticmethod
    @transaction.atomic
    def mark_failed(
        event: IntegrationEvent,
        error: Exception,
        include_traceback: bool = True
    ) -> IntegrationEvent:
        """Mark an event as failed."""
        error_message = str(error)
        error_traceback = traceback.format_exc() if include_traceback else ''
        
        event.mark_failed(error_message, error_traceback)
        
        logger.error(
            f"Event {event.id} marked as failed: {error_message}",
            exc_info=include_traceback
        )
        
        return event
    
    @staticmethod
    @transaction.atomic
    def retry_event(event: IntegrationEvent) -> IntegrationEvent:
        """Increment retry count and mark for retry."""
        event.retry()
        
        logger.info(f"Event {event.id} marked for retry (attempt {event.retry_count})")
        
        return event
    
    @staticmethod
    def get_recent_events(
        limit: int = 100,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        source_system: Optional[str] = None
    ) -> List[IntegrationEvent]:
        """Get recent integration events with optional filters."""
        queryset = IntegrationEvent.objects.all()
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if status:
            queryset = queryset.filter(status=status)
        if source_system:
            queryset = queryset.filter(source_system=source_system)
        
        return list(queryset[:limit])
    
    @staticmethod
    @staticmethod
    def get_failed_events(max_retries: int = 3) -> List[IntegrationEvent]:
        """Get failed events that haven't exceeded max retries."""
        return list(
            IntegrationEvent.objects.filter(
                status=IntegrationEvent.Status.FAILED
            ).order_by('-created_at')
        )
    
    @staticmethod
    def get_statistics(
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict[str, Any]:
        """Get integration event statistics."""
        from django.db.models import Count, Avg, Q
        
        queryset = IntegrationEvent.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        stats = queryset.aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status=IntegrationEvent.Status.PROCESSED)),
            failed=Count('id', filter=Q(status=IntegrationEvent.Status.FAILED)),
            pending=Count('id', filter=Q(status=IntegrationEvent.Status.RECEIVED))
        )
        
        stats['success_rate'] = (
            (stats['success'] / stats['total'] * 100)
            if stats['total'] > 0 else 0
        )
        
        return stats


class AuditLogService:
    """Service for managing audit logs."""
    
    @staticmethod
    @transaction.atomic
    def log_action(
        action: str,
        model_name: str,
        object_id: str,
        user: Optional[User] = None,
        changes: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        request=None
    ) -> AuditLog:
        """
        Log an action in the audit trail.
        
        Args:
            action: Action type (from AuditLog.Action)
            model_name: Name of the model
            object_id: ID of the object
            user: User who performed the action
            changes: Dict with before/after values
            metadata: Additional metadata
            request: Django request object (for IP, user agent)
            
        Returns:
            AuditLog instance
        """
        ip_address = None
        user_agent = ''
        
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        audit_log = AuditLog.objects.create(
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            user=user,
            changes=changes or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            f"Audit log created: {user} - {action} - {model_name} #{object_id}"
        )
        
        return audit_log
    
    @staticmethod
    def log_create(
        model_name: str,
        object_id: str,
        user: Optional[User] = None,
        metadata: Optional[Dict] = None,
        request=None
    ) -> AuditLog:
        """Log object creation."""
        return AuditLogService.log_action(
            action=AuditLog.Action.CREATE,
            model_name=model_name,
            object_id=object_id,
            user=user,
            metadata=metadata,
            request=request
        )
    
    @staticmethod
    def log_update(
        model_name: str,
        object_id: str,
        changes: Dict[str, Any],
        user: Optional[User] = None,
        metadata: Optional[Dict] = None,
        request=None
    ) -> AuditLog:
        """Log object update with changes."""
        return AuditLogService.log_action(
            action=AuditLog.Action.UPDATE,
            model_name=model_name,
            object_id=object_id,
            user=user,
            changes=changes,
            metadata=metadata,
            request=request
        )
    
    @staticmethod
    def log_delete(
        model_name: str,
        object_id: str,
        user: Optional[User] = None,
        metadata: Optional[Dict] = None,
        request=None
    ) -> AuditLog:
        """Log object deletion."""
        return AuditLogService.log_action(
            action=AuditLog.Action.DELETE,
            model_name=model_name,
            object_id=object_id,
            user=user,
            metadata=metadata,
            request=request
        )
    
    @staticmethod
    def get_object_history(
        model_name: str,
        object_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit history for a specific object."""
        return list(
            AuditLog.objects.filter(
                model_name=model_name,
                object_id=str(object_id)
            ).order_by('-created_at')[:limit]
        )
    
    @staticmethod
    def get_user_activity(
        user: User,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent activity for a specific user."""
        return list(
            AuditLog.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
        )


class IntegrationContextManager:
    """
    Context manager for tracking integration operations.
    
    Usage:
        with IntegrationContextManager(
            event_type=IntegrationEvent.EventType.GOODGRANTS_SYNC,
            source_system='goodgrants',
            destination_system='django',
            external_id=gg_id,
            request_data=payload
        ) as event:
            # Do integration work
            result = do_sync()
            event.response_data = result
    """
    
    def __init__(
        self,
        event_type: str,
        source_system: str,
        destination_system: str = '',
        external_id: str = '',
        internal_id: str = '',
        request_data: Optional[Dict] = None,
        user: Optional[User] = None
    ):
        self.event_type = event_type
        self.source_system = source_system
        self.destination_system = destination_system
        self.external_id = external_id
        self.internal_id = internal_id
        self.request_data = request_data
        self.user = user
        self.event = None
        self.start_time = None
    
    def __enter__(self) -> IntegrationEvent:
        """Create event and start timer."""
        self.start_time = time.time()
        self.event = IntegrationEventService.create_event(
            event_type=self.event_type,
            source_system=self.source_system,
            destination_system=self.destination_system,
            external_id=self.external_id,
            internal_id=self.internal_id,
            request_data=self.request_data,
            user=self.user
        )
        return self.event
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Mark event as success or failure based on exception."""
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is None:
            # Success
            IntegrationEventService.mark_success(
                self.event,
                response_data=getattr(self.event, 'response_data', None),
                duration_ms=duration_ms
            )
        else:
            # Failure
            IntegrationEventService.mark_failed(
                self.event,
                exc_val,
                include_traceback=True
            )
        
        # Don't suppress exceptions
        return False