import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["AuditHawk"]

audit_reports_col = db["audit_reports"]
transactions_col = db["transactions"]
flagged_transactions_col = db["flagged_transactions"]
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
