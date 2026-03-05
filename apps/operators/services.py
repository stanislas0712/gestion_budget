"""
Business logic services for operators app.
Gestion des opérateurs (organisations bénéficiaires).
"""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from .models import Operator
from apps.audits.services import AuditLogService, IntegrationContextManager
from apps.audits.models import IntegrationEvent, AuditLog

logger = logging.getLogger(__name__)


class OperatorService:
    """Service for managing operators."""
    
    @staticmethod
    @transaction.atomic
    def create_operator(
        data: Dict[str, Any],
        user: Optional[User] = None,
        request=None
    ) -> Operator:
        """
        Create a new operator.
        
        Args:
            data: Operator data
            user: User creating the operator
            request: Django request for audit logging
            
        Returns:
            Operator instance
        """
        operator = Operator.objects.create(
            **data,
            created_by=user
        )
        
        # Log creation
        AuditLogService.log_create(
            model_name='Operator',
            object_id=str(operator.id),
            user=user,
            metadata={'name': operator.name},
            request=request
        )
        
        logger.info(f"Created operator {operator.name} (ID: {operator.id})")
        
        return operator
    
    @staticmethod
    @transaction.atomic
    def update_operator(
        operator: Operator,
        data: Dict[str, Any],
        user: Optional[User] = None,
        request=None
    ) -> Operator:
        """
        Update an existing operator.
        
        Args:
            operator: Operator instance
            data: Updated data
            user: User updating the operator
            request: Django request for audit logging
            
        Returns:
            Updated operator instance
        """
        # Track changes for audit
        changes = {}
        for key, value in data.items():
            old_value = getattr(operator, key, None)
            if old_value != value:
                changes[key] = {'before': old_value, 'after': value}
                setattr(operator, key, value)
        
        operator.save()
        
        # Log update
        if changes:
            AuditLogService.log_update(
                model_name='Operator',
                object_id=str(operator.id),
                changes=changes,
                user=user,
                request=request
            )
        
        logger.info(f"Updated operator {operator.name} (ID: {operator.id})")
        
        return operator
    
    @staticmethod
    @transaction.atomic
    def verify_operator(
        operator: Operator,
        user: Optional[User] = None,
        request=None
    ) -> Operator:
        """
        Verify an operator.
        
        Args:
            operator: Operator instance
            user: User verifying the operator
            request: Django request for audit logging
            
        Returns:
            Verified operator
        """
        operator.verify()
        
        # Log verification
        AuditLogService.log_action(
            action=AuditLog.Action.APPROVE,
            model_name='Operator',
            object_id=str(operator.id),
            user=user,
            metadata={'action': 'verified'},
            request=request
        )
        
        logger.info(f"Verified operator {operator.name} (ID: {operator.id})")
        
        return operator
    
    @staticmethod
    @transaction.atomic
    def sync_to_odoo(
        operator: Operator,
        user: Optional[User] = None
    ) -> int:
        """
        Synchronize operator to Odoo as a partner.
        
        Args:
            operator: Operator instance
            user: User triggering the sync
            
        Returns:
            Odoo partner ID
        """
        from apps.integrations.odoo.services import OdooOperatorSync
        from apps.integrations.odoo.serializers import OdooOperatorSerializer
        
        with IntegrationContextManager(
            event_type=IntegrationEvent.EventType.ODOO_CREATE if not operator.odoo_partner_id else IntegrationEvent.EventType.ODOO_UPDATE,
            source_system='django',
            destination_system='odoo',
            internal_id=str(operator.id),
            external_id=operator.gg_operator_id,
            request_data={'operator_id': operator.id, 'name': operator.name},
            user=user
        ) as event:
            sync_service = OdooOperatorSync()
            operator_data = OdooOperatorSerializer.to_odoo(operator)
            
            if operator.odoo_partner_id:
                # Update existing partner
                sync_service.write('res.partner', [operator.odoo_partner_id], operator_data)
                partner_id = operator.odoo_partner_id
            else:
                # Create new partner
                partner_id = sync_service.create('res.partner', operator_data)
                operator.odoo_partner_id = partner_id
            
            operator.last_synced_at = timezone.now()
            operator.save()
            
            event.response_data = {'partner_id': partner_id}
            
            logger.info(
                f"Synced operator {operator.name} to Odoo (Partner ID: {partner_id})"
            )
            
            return partner_id
    
    @staticmethod
    def sync_from_goodgrants(
        gg_operator_id: str,
        user: Optional[User] = None
    ) -> Operator:
        """
        Sync an operator from GoodGrants.
        
        Args:
            gg_operator_id: GoodGrants operator ID
            user: User triggering the sync
            
        Returns:
            Operator instance
        """
        from apps.integrations.goodgrants.services import GoodGrantsOperatorSync
        
        with IntegrationContextManager(
            event_type=IntegrationEvent.EventType.GOODGRANTS_SYNC,
            source_system='goodgrants',
            destination_system='django',
            external_id=gg_operator_id,
            user=user
        ) as event:
            sync_service = GoodGrantsOperatorSync()
            gg_data = sync_service.get_operator_info(gg_operator_id)
            
            # Check if operator already exists
            operator, created = Operator.objects.update_or_create(
                gg_operator_id=gg_operator_id,
                defaults={
                    'name': gg_data.get('name', ''),
                    'legal_name': gg_data.get('legal_name', ''),
                    'email': gg_data.get('email', ''),
                    'phone': gg_data.get('phone', ''),
                    'address': gg_data.get('address', ''),
                    'city': gg_data.get('city', ''),
                    'country': gg_data.get('country', ''),
                    'raw_data': gg_data,
                    'last_synced_at': timezone.now(),
                    'created_by': user if created else None,
                }
            )
            
            event.internal_id = str(operator.id)
            event.response_data = {'operator_id': operator.id, 'created': created}
            
            action = 'Created' if created else 'Updated'
            logger.info(f"{action} operator {operator.name} from GoodGrants")
            
            return operator
    
    @staticmethod
    def get_active_operators() -> List[Operator]:
        """Get all active operators."""
        return list(
            Operator.objects.filter(
                status=Operator.Status.ACTIVE
            ).order_by('name')
        )
    
    @staticmethod
    def get_unverified_operators() -> List[Operator]:
        """Get operators that need verification."""
        return list(
            Operator.objects.filter(
                is_verified=False,
                status=Operator.Status.ACTIVE
            ).order_by('created_at')
        )
    
    @staticmethod
    def get_operators_not_synced_to_odoo() -> List[Operator]:
        """Get operators not yet synced to Odoo."""
        return list(
            Operator.objects.filter(
                odoo_partner_id__isnull=True,
                status=Operator.Status.ACTIVE
            ).order_by('created_at')
        )
    
    @staticmethod
    def search_operators(query: str) -> List[Operator]:
        """
        Search operators by name, email, or city.
        
        Args:
            query: Search query
            
        Returns:
            List of matching operators
        """
        from django.db.models import Q
        
        return list(
            Operator.objects.filter(
                Q(name__icontains=query) |
                Q(legal_name__icontains=query) |
                Q(email__icontains=query) |
                Q(city__icontains=query) |
                Q(gg_operator_id__icontains=query)
            ).distinct()
        )
    
    @staticmethod
    def get_operator_statistics() -> Dict[str, Any]:
        """Get operator statistics."""
        from django.db.models import Count
        
        total = Operator.objects.count()
        by_status = Operator.objects.values('status').annotate(count=Count('id'))
        by_type = Operator.objects.values('type').annotate(count=Count('id'))
        
        verified_count = Operator.objects.filter(is_verified=True).count()
        synced_to_odoo = Operator.objects.filter(odoo_partner_id__isnull=False).count()
        
        return {
            'total': total,
            'by_status': {item['status']: item['count'] for item in by_status},
            'by_type': {item['type']: item['count'] for item in by_type},
            'verified': verified_count,
            'synced_to_odoo': synced_to_odoo,
            'verification_rate': (verified_count / total * 100) if total > 0 else 0,
            'odoo_sync_rate': (synced_to_odoo / total * 100) if total > 0 else 0,
        }