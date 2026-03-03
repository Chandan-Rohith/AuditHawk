import graphene
import jwt
import os
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import datetime, timedelta
from pymongo import ReturnDocument
from .csv_parser import parse_transaction_csv, CSVParserError
from .ml_engine.ensemble import run_pipeline

from .db import (
    audit_reports_col, transactions_col, flagged_transactions_col,
    users_col, trusted_vendors_col,
    get_trusted_vendors, add_trusted_vendor, remove_trusted_vendor,
)

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_jwt(user):
    """Generate a JWT token for a given Django user."""
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ============================================
# GraphQL Types (Business Entities)
# ============================================

class TransactionType(graphene.ObjectType):
    """Represents a single transaction from CSV"""
    id = graphene.ID()
    transaction_id = graphene.String()
    date = graphene.String()
    amount = graphene.Float()
    merchant = graphene.String()
    category = graphene.String()
    account_id = graphene.String()


class AuditReportType(graphene.ObjectType):
    """Represents an uploaded audit file and its processing status"""
    id = graphene.ID()
    file_name = graphene.String()
    uploaded_at = graphene.String()
    total_transactions = graphene.Int()
    flagged_count = graphene.Int()
    status = graphene.String()


class FlaggedTransactionType(graphene.ObjectType):
    """Represents a suspicious transaction detected by the system"""
    id = graphene.ID()
    transaction_id = graphene.String()
    amount = graphene.Float()
    risk_score = graphene.Float()
    decision = graphene.String()
    explanation = graphene.String()  # XAI reasoning


# ============================================
# Mock Data (In-Memory Storage) - REPLACED WITH MONGODB
# ============================================
# All data is now stored in MongoDB collections:
# - audit_reports_col
# - transactions_col
# - flagged_transactions_col

class DashboardSummaryType(graphene.ObjectType):
    total_reports = graphene.Int()
    total_transactions = graphene.Int()
    total_flagged = graphene.Int()
    processing_count = graphene.Int()
    completed_count = graphene.Int()
# ============================================
# Query Resolvers
# ============================================

class Query(graphene.ObjectType):
    """Root query for AuditHawk GraphQL API"""

    hello = graphene.String(default_value="Hello AuditHawk!")

    audit_reports = graphene.List(AuditReportType)
    transactions = graphene.List(
        TransactionType,
        report_id=graphene.ID(required=True)
    )
    flagged_transactions = graphene.List(
        FlaggedTransactionType,
        report_id=graphene.ID(required=True)
    )
    dashboard_summary = graphene.Field(DashboardSummaryType)

    def resolve_audit_reports(root, info):
        reports = audit_reports_col.find()
        return [
            AuditReportType(
                id=str(r["_id"]),
                file_name=r["file_name"],
                uploaded_at=r["uploaded_at"],
                total_transactions=r["total_transactions"],
                flagged_count=r["flagged_count"],
                status=r["status"]
            )
            for r in reports
        ]


    def resolve_transactions(root, info, report_id):
        transactions = transactions_col.find({"report_id": report_id})
        return [
            TransactionType(
                id=str(txn["_id"]),
                transaction_id=txn["transaction_id"],
                date=txn["date"],
                amount=txn["amount"],
                merchant=txn["merchant"],
                category=txn["category"],
                account_id=txn["account_id"]
            )
            for txn in transactions
        ]

    def resolve_flagged_transactions(root, info, report_id):
        transactions = flagged_transactions_col.find({"report_id": report_id})
        return [
            FlaggedTransactionType(
                id=str(txn["_id"]),
                transaction_id=txn["transaction_id"],
                amount=txn["amount"],
                risk_score=txn["risk_score"],
                decision=txn["decision"],
                explanation=txn["explanation"]
            )
            for txn in transactions
        ]

    def resolve_dashboard_summary(root, info):
        reports = list(audit_reports_col.find())
        
        total_reports = len(reports)
        total_transactions = sum(report.get("total_transactions", 0) for report in reports)
        total_flagged = sum(report.get("flagged_count", 0) for report in reports)
        processing_count = sum(1 for report in reports if report.get("status") == "processing")
        completed_count = sum(1 for report in reports if report.get("status") == "completed")

        return DashboardSummaryType(
            total_reports=total_reports,
            total_transactions=total_transactions,
            total_flagged=total_flagged,
            processing_count=processing_count,
            completed_count=completed_count
        )



# ============================================
# Mutation Types
# ============================================

class UploadAuditFileResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    report = graphene.Field(AuditReportType)


class UploadAuditFile(graphene.Mutation):
    """
    Upload and parse a CSV file containing financial transactions.
    This is the ONLY way to upload data - no REST endpoints are used.
    """
    class Arguments:
        file_name = graphene.String(required=True)
        csv_content = graphene.String(required=True)

    Output = UploadAuditFileResponse

    def mutate(root, info, file_name, csv_content):
        """
        Parse CSV content, validate it, and create an audit report.
        
        Args:
            file_name: Name of the CSV file (e.g., "transactions.csv")
            csv_content: Complete CSV file content as a string
            
        Returns:
            UploadAuditFileResponse with success status, message, and report
        """
        try:
            # Parse and validate CSV content using csv_parser
            transactions, summary = parse_transaction_csv(csv_content)
            
            # Create new audit report in MongoDB
            new_report = {
                "file_name": file_name,
                "uploaded_at": datetime.utcnow().isoformat(),
                "total_transactions": summary['total_transactions'],
                "flagged_count": 0,  # Will be updated after ML analysis
                "status": "processing"
            }
            
            # Insert report into MongoDB
            result = audit_reports_col.insert_one(new_report)
            report_id = str(result.inserted_id)
            
            # Store transactions in MongoDB with report_id reference
            for txn in transactions:
                txn['report_id'] = report_id
            transactions_col.insert_many(transactions)

            # ── Run ML ensemble pipeline automatically ──────────
            try:
                trusted = get_trusted_vendors()
                flagged_docs = run_pipeline(transactions, report_id, trusted)
                if flagged_docs:
                    flagged_transactions_col.insert_many(flagged_docs)
                flagged_count = len(flagged_docs)
                audit_reports_col.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"flagged_count": flagged_count, "status": "completed"}},
                )
                new_report["flagged_count"] = flagged_count
                new_report["status"] = "completed"
            except Exception as ml_err:
                # ML failure should not break the upload
                audit_reports_col.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"status": "completed", "ml_error": str(ml_err)}},
                )
                new_report["status"] = "completed"

            return UploadAuditFileResponse(
                success=True,
                message=f"Successfully uploaded and analyzed {summary['total_transactions']} transactions ({new_report['flagged_count']} flagged)",
                report=AuditReportType(
                    id=report_id,
                    file_name=new_report["file_name"],
                    uploaded_at=new_report["uploaded_at"],
                    total_transactions=new_report["total_transactions"],
                    flagged_count=new_report["flagged_count"],
                    status=new_report["status"]
                )
            )
            
        except CSVParserError as e:
            # Handle CSV parsing/validation errors
            return UploadAuditFileResponse(
                success=False,
                message=f"CSV parsing error: {str(e)}",
                report=None
            )
        except Exception as e:
            # Handle unexpected errors
            return UploadAuditFileResponse(
                success=False,
                message=f"Unexpected error: {str(e)}",
                report=None
            )


class UpdateTransactionDecisionResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    transaction = graphene.Field(FlaggedTransactionType)


class UpdateTransactionDecision(graphene.Mutation):
    """Update the decision on a flagged transaction (approve/reject/escalate)"""
    
    class Arguments:
        report_id = graphene.ID(required=True)
        transaction_id = graphene.String(required=True)
        decision = graphene.String(required=True)  # approved, rejected, escalate
    
    Output = UpdateTransactionDecisionResponse
    
    def mutate(root, info, report_id, transaction_id, decision):
        # Validate decision
        valid_decisions = ['approved', 'rejected', 'escalate', 'review_required', 'monitor']
        if decision not in valid_decisions:
            return UpdateTransactionDecisionResponse(
                success=False,
                message=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}",
                transaction=None
            )
        
        # Find and update the flagged transaction in MongoDB
        result = flagged_transactions_col.find_one_and_update(
            {"report_id": report_id, "transaction_id": transaction_id},
            {"$set": {"decision": decision}},
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            return UpdateTransactionDecisionResponse(
                success=False,
                message=f"Transaction {transaction_id} not found in report {report_id}",
                transaction=None
            )
        
        return UpdateTransactionDecisionResponse(
            success=True,
            message=f"Transaction decision updated to '{decision}'",
            transaction=FlaggedTransactionType(
                id=str(result["_id"]),
                transaction_id=result["transaction_id"],
                amount=result["amount"],
                risk_score=result["risk_score"],
                decision=result["decision"],
                explanation=result["explanation"]
            )
        )


# ============================================
# User / Auth Types & Mutations
# ============================================


class UserType(graphene.ObjectType):
    id = graphene.ID()
    email = graphene.String()
    provider = graphene.String()
    created_at = graphene.String()


class AuthResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()
    user = graphene.Field(UserType)


class CreateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=False)

    Output = AuthResponse

    def mutate(root, info, email, password, name=None):
        User = get_user_model()
        if User.objects.filter(username=email).exists():
            return AuthResponse(success=False, message="User already exists", token=None, user=None)

        user = User.objects.create_user(username=email, email=email)
        user.set_password(password)
        if name:
            user.first_name = name
        user.save()

        profile = {
            "email": email,
            "provider": "local",
            "created_at": timezone.now().isoformat(),
        }
        users_col.insert_one(profile)

        token = generate_jwt(user)
        return AuthResponse(
            success=True,
            message="User created successfully",
            token=token,
            user=UserType(id=str(user.id), email=user.email, provider="local", created_at=profile["created_at"])
        )


class LoginUser(graphene.Mutation):
    """Authenticate an existing user with email + password."""
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = AuthResponse

    def mutate(root, info, email, password):
        user = authenticate(username=email, password=password)
        if user is None:
            return AuthResponse(success=False, message="Invalid email or password", token=None, user=None)

        # Record login in MongoDB
        users_col.update_one(
            {"email": email},
            {"$set": {"last_login": timezone.now().isoformat()}},
            upsert=True,
        )

        token = generate_jwt(user)
        return AuthResponse(
            success=True,
            message="Login successful",
            token=token,
            user=UserType(id=str(user.id), email=user.email, provider="local", created_at=None)
        )


# ============================================
# ML Re-Analysis Mutation
# ============================================

class AnalyzeReportResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    flagged_count = graphene.Int()


class AnalyzeReport(graphene.Mutation):
    """Re-run the ML ensemble pipeline on an existing report."""
    class Arguments:
        report_id = graphene.ID(required=True)

    Output = AnalyzeReportResponse

    def mutate(root, info, report_id):
        from bson import ObjectId
        report = audit_reports_col.find_one({"_id": ObjectId(report_id)})
        if not report:
            return AnalyzeReportResponse(success=False, message="Report not found", flagged_count=0)

        txns = list(transactions_col.find({"report_id": report_id}))
        if not txns:
            return AnalyzeReportResponse(success=False, message="No transactions for this report", flagged_count=0)

        # Clear previous flags
        flagged_transactions_col.delete_many({"report_id": report_id})

        trusted = get_trusted_vendors()
        flagged_docs = run_pipeline(txns, report_id, trusted)
        if flagged_docs:
            flagged_transactions_col.insert_many(flagged_docs)

        audit_reports_col.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"flagged_count": len(flagged_docs), "status": "completed"}},
        )

        return AnalyzeReportResponse(
            success=True,
            message=f"Re-analysis complete: {len(flagged_docs)} anomalies detected",
            flagged_count=len(flagged_docs),
        )


# ============================================
# Trusted Vendor Mutations (HITL Masking)
# ============================================

class TrustedVendorResponse(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    vendors = graphene.List(graphene.String)


class AddTrustedVendor(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    Output = TrustedVendorResponse

    def mutate(root, info, name):
        ok = add_trusted_vendor(name)
        vendors = get_trusted_vendors()
        return TrustedVendorResponse(
            success=ok,
            message=f"'{name}' added to trusted vendors" if ok else "Invalid vendor name",
            vendors=vendors,
        )


class RemoveTrustedVendor(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    Output = TrustedVendorResponse

    def mutate(root, info, name):
        ok = remove_trusted_vendor(name)
        vendors = get_trusted_vendors()
        return TrustedVendorResponse(
            success=ok,
            message=f"'{name}' removed from trusted vendors" if ok else "Vendor not found",
            vendors=vendors,
        )


class Mutation(graphene.ObjectType):
    upload_audit_file = UploadAuditFile.Field()
    update_transaction_decision = UpdateTransactionDecision.Field()
    # ML pipeline
    analyze_report = AnalyzeReport.Field()
    # HITL Trusted Vendors
    add_trusted_vendor = AddTrustedVendor.Field()
    remove_trusted_vendor = RemoveTrustedVendor.Field()
    # Authentication / user management
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()


# ============================================
# Schema Export
# ============================================

schema = graphene.Schema(query=Query, mutation=Mutation)
