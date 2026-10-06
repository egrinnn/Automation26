from flask import Blueprint, render_template, request

from app.decorators import admin_required
from app.models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/admin/audit')


@audit_bp.route('/')
@admin_required
def list_audit():
    entity_type = request.args.get('entity_type')
    query = AuditLog.query
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    entries = query.order_by(AuditLog.created_at.desc()).limit(300).all()
    entity_types = ['category', 'dish', 'menu']
    return render_template(
        'audit/list.html',
        entries=entries,
        entity_types=entity_types,
        selected_entity_type=entity_type,
    )
