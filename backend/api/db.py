import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["AuditHawk"]

audit_reports_col = db["audit_reports"]
transactions_col = db["transactions"]

# New: store uploaded CSVs as a single batch document containing all transactions
transaction_batches_col = db["transaction_batches"]

# Legacy collection `flagged_transactions` has been consolidated into
# `transactions`. Use `transactions_col` for all reads/writes and filter
# on the `flagged` boolean. The legacy collection is removed by the
# migration script when --drop-legacy is used.

users_col = db["users"]
trusted_vendors_col = db["trusted_vendors"]


# ── Trusted-vendor helpers (HITL Active Learning / Masking) ──

def get_trusted_vendors() -> list[str]:
    """Return a flat list of trusted vendor names from MongoDB."""
    docs = trusted_vendors_col.find({}, {"name": 1, "_id": 0})
    return [d["name"] for d in docs if "name" in d]


def add_trusted_vendor(name: str) -> bool:
    """Add a vendor to the trusted whitelist (idempotent)."""
    name = name.strip()
    if not name:
        return False
    trusted_vendors_col.update_one(
        {"name": name},
        {"$set": {"name": name}},
        upsert=True,
    )
    return True


def remove_trusted_vendor(name: str) -> bool:
    """Remove a vendor from the trusted whitelist."""
    result = trusted_vendors_col.delete_one({"name": name.strip()})
    return result.deleted_count > 0


# Ensure recommended indexes exist (idempotent). This helps queries stay fast
# and runs safely on module import.
def _ensure_indexes():
    try:
        transactions_col.create_index([("user_id", 1), ("report_id", 1), ("flagged", 1)])
        transaction_batches_col.create_index([("user_id", 1), ("report_id", 1)])
        transactions_col.create_index([("created_at", -1)])
        trusted_vendors_col.create_index("name", unique=True, sparse=True)
        audit_reports_col.create_index([("user_id", 1), ("created_at", -1)])
        # Ensure an index to speed up user lookups; keep unique constraint off
        users_col.create_index("email", sparse=True)
    except Exception:
        # Avoid crashing on import; index creation will be retried by script.
        pass


# Run index setup in background when module is imported
_ensure_indexes()
