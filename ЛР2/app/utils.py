from flask_login import current_user
from app.extensions import db
from app.models import AuditLog


def log_action(action: str, entity_type: str, entity_id: int, details: str | None = None) -> None:
    entry = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.session.add(entry)
