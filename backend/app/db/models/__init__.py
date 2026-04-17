"""Import every model so Alembic's autogenerate sees them."""
from app.db.models.audit import AuditLog
from app.db.models.call import Call, CallTurn
from app.db.models.customer import Customer
from app.db.models.document import Alert, Document, DocumentExtraction
from app.db.models.task import Task
from app.db.models.tenant import Subscription, Tenant
from app.db.models.user import Invite, User

__all__ = [
    "Alert",
    "AuditLog",
    "Call",
    "CallTurn",
    "Customer",
    "Document",
    "DocumentExtraction",
    "Invite",
    "Subscription",
    "Task",
    "Tenant",
    "User",
]
