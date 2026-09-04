"""把模型集中导出，Alembic 和 create_all 才能看到所有表。"""

from app.models.contract import Contract
from app.models.document import ContractFile, ImportBatch
from app.models.invoice import Invoice
from app.models.payment import Collection, PaymentSchedule
from app.models.user import User

__all__ = [
    "User",
    "Contract",
    "Invoice",
    "ImportBatch",
    "ContractFile",
    "PaymentSchedule",
    "Collection",
]
