from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionType(str, Enum):
    deposit = "deposit"
    debt = "debt"


class TransactionStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    failed = "failed"


class PredictionStatus(str, Enum):
    waiting = "waiting"
    processed = "processed"
    ready = "ready"
    cancel = "cancel"
    failed = "failed"
