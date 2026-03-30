"""
AuditHawk – Flask Frontend
Serves Jinja2-rendered pages and proxies auth requests to the Django GraphQL backend.
"""

import os
import requests as http_requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "audithawk-flask-secret-change-me")

try:
    app.config["MAX_UPLOAD_BYTES"] = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
except (TypeError, ValueError):
    app.config["MAX_UPLOAD_BYTES"] = 5 * 1024 * 1024

# Django backend GraphQL endpoint
GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://localhost:8000/graphql/")



# ── helpers ──────────────────────────────────────────────

def _extract_graphql_data(resp: http_requests.Response) -> dict:
    try:
        payload = resp.json()
    except ValueError:
        raw = (resp.text or "").strip()
        details = raw[:200] if raw else "empty response"
        raise Exception(f"Backend returned non-JSON response (status {resp.status_code}): {details}")

    if not isinstance(payload, dict):
        raise Exception(f"Backend returned invalid response type: {type(payload).__name__}")

    if payload.get("errors"):
        first_error = payload["errors"][0] if isinstance(payload["errors"], list) else payload["errors"]
        if isinstance(first_error, dict):
            message = first_error.get("message") or "GraphQL error"
        else:
            message = str(first_error)
        raise Exception(message)

    data = payload.get("data")
    if data is None:
        raise Exception("Backend response missing 'data' field")
    return data

def gql(query: str, variables: dict | None = None) -> dict:
    """Send a GraphQL request to the Django backend."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        resp = http_requests.post(
            GRAPHQL_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
    except http_requests.RequestException as e:
        raise Exception(f"Unable to reach backend at {GRAPHQL_URL}: {e}")

    return _extract_graphql_data(resp)


def _auth_headers() -> dict:
    token = session.get("token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def gql_auth(query: str, variables: dict | None = None) -> dict:
    """Send a GraphQL request with user auth token when available."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        resp = http_requests.post(
            GRAPHQL_URL,
            json=payload,
            headers=_auth_headers(),
            timeout=120,
        )
    except http_requests.RequestException as e:
        raise Exception(f"Unable to reach backend at {GRAPHQL_URL}: {e}")

    return _extract_graphql_data(resp)


def login_required(f):
    """Decorator: redirect to /auth if no session token."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "token" not in session:
            return redirect(url_for("auth_page"))
        return f(*args, **kwargs)

    return decorated


# ── routes ───────────────────────────────────────────────

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/auth")
def auth_page():
    return render_template("auth.html")


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Proxy login to Django GraphQL."""
    body = request.get_json(force=True)
    email = body.get("email", "")
    password = body.get("password", "")
    try:
        data = gql(
            """mutation($email:String!,$password:String!){
                loginUser(email:$email,password:$password){
                    success message token user{ id email provider }
                }
            }""",
            {"email": email, "password": password},
        )
        result = data["loginUser"]
        if result["success"]:
            session["token"] = result["token"]
            session["user"] = result["user"]
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    """Proxy signup to Django GraphQL."""
    body = request.get_json(force=True)
    email = body.get("email", "")
    password = body.get("password", "")
    try:
        data = gql(
            """mutation($email:String!,$password:String!){
                createUser(email:$email,password:$password){
                    success message token user{ id email provider }
                }
            }""",
            {"email": email, "password": password},
        )
        result = data["createUser"]
        if result["success"]:
            session["token"] = result["token"]
            session["user"] = result["user"]
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/app")
@app.route("/dashboard")
@login_required
def main_app():
    user = session.get("user", {})
    return render_template("main.html", user=user)


@app.route("/api/vendors", methods=["GET"])
@login_required
def api_get_vendors():
    try:
        data = gql_auth("""query { trustedVendors }""")
        return jsonify({"success": True, "vendors": data.get("trustedVendors", [])})
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "vendors": []}), 500


@app.route("/api/vendors", methods=["POST"])
@login_required
def api_add_vendor():
    body = request.get_json(force=True)
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "Vendor name is required.", "vendors": []}), 400

    try:
        data = gql_auth(
            """mutation($name:String!){
                addTrustedVendor(name:$name){ success message vendors }
            }""",
            {"name": name},
        )
        result = data.get("addTrustedVendor") or {}
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "vendors": []}), 500


@app.route("/api/vendors/<path:name>", methods=["DELETE"])
@login_required
def api_remove_vendor(name):
    clean_name = (name or "").strip()
    if not clean_name:
        return jsonify({"success": False, "message": "Vendor name is required.", "vendors": []}), 400

    try:
        data = gql_auth(
            """mutation($name:String!){
                removeTrustedVendor(name:$name){ success message vendors }
            }""",
            {"name": clean_name},
        )
        result = data.get("removeTrustedVendor") or {}
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "vendors": []}), 500


@app.route("/api/audit/upload", methods=["POST"])
@login_required
def api_upload_audit():
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "message": "CSV file is required."}), 400

    raw_filename = (file.filename or "").strip()
    safe_filename = secure_filename(raw_filename)
    if not raw_filename or not safe_filename:
        return jsonify({"success": False, "message": "Invalid file name."}), 400

    max_upload_bytes = app.config.get("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)
    content_length = request.content_length
    if content_length is not None and content_length > max_upload_bytes:
        return jsonify({"success": False, "message": f"File is too large. Maximum size is {max_upload_bytes} bytes."}), 400

    try:
        file.stream.seek(0, os.SEEK_END)
        file_size = file.stream.tell()
        file.stream.seek(0)
    except Exception:
        file_size = None

    if file_size is not None and file_size > max_upload_bytes:
        return jsonify({"success": False, "message": f"File is too large. Maximum size is {max_upload_bytes} bytes."}), 400

    threshold_raw = (request.form.get("thresholdLimit") or "").strip()
    threshold_limit = None
    if threshold_raw:
        try:
            threshold_limit = float(threshold_raw)
            if threshold_limit <= 0:
                return jsonify({"success": False, "message": "Threshold must be greater than 0."}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Threshold must be a valid number."}), 400

    try:
        csv_content = file.read().decode("utf-8")
    except Exception:
        return jsonify({"success": False, "message": "Unable to read CSV file as UTF-8."}), 400

    try:
        data = gql_auth(
            """mutation($fileName:String!,$csvContent:String!,$thresholdLimit:Float){
                uploadAuditFile(fileName:$fileName,csvContent:$csvContent,thresholdLimit:$thresholdLimit){
                    success
                    message
                    report{ id fileName uploadedAt totalTransactions flaggedCount status }
                }
            }""",
            {
                "fileName": safe_filename,
                "csvContent": csv_content,
                "thresholdLimit": threshold_limit,
            },
        )
        result = data.get("uploadAuditFile") or {}
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/reports", methods=["GET"])
@login_required
def api_reports():
    try:
        data = gql_auth(
            """query {
                auditReports {
                    id
                    fileName
                    uploadedAt
                    totalTransactions
                    flaggedCount
                    status
                }
            }"""
        )
        reports = data.get("auditReports") or []
        reports = sorted(reports, key=lambda r: r.get("uploadedAt") or "", reverse=True)
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "reports": []}), 500


@app.route("/api/reports/<report_id>", methods=["GET"])
@login_required
def api_report_details(report_id):
    try:
        data = gql_auth(
            """query($reportId:ID!){
                transactions(reportId:$reportId){
                    id
                    transactionId
                    date
                    amount
                    merchant
                    category
                    accountId
                }
                flaggedTransactions(reportId:$reportId){
                    id
                    transactionId
                    amount
                    riskScore
                    decision
                    explanation
                }
            }""",
            {"reportId": report_id},
        )
        return jsonify({
            "success": True,
            "transactions": data.get("transactions") or [],
            "frauds": data.get("flaggedTransactions") or [],
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "transactions": [], "frauds": []}), 500


@app.route("/api/reports/<report_id>/analyze", methods=["POST"])
@login_required
def api_reanalyze_report(report_id):
    try:
        data = gql_auth(
            """mutation($reportId:ID!){
                analyzeReport(reportId:$reportId){
                    success
                    message
                    flaggedCount
                }
            }""",
            {"reportId": report_id},
        )
        result = data.get("analyzeReport") or {}
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "flaggedCount": 0}), 500


@app.route("/api/flagged/decision", methods=["POST"])
@login_required
def api_update_flagged_decision():
    body = request.get_json(force=True)
    report_id = body.get("reportId")
    transaction_id = body.get("transactionId")
    decision = body.get("decision")

    if not report_id or not transaction_id or not decision:
        return jsonify({"success": False, "message": "reportId, transactionId and decision are required."}), 400

    try:
        data = gql_auth(
            """mutation($reportId:ID!,$transactionId:String!,$decision:String!){
                updateTransactionDecision(reportId:$reportId,transactionId:$transactionId,decision:$decision){
                    success
                    message
                    transaction {
                        id
                        transactionId
                        amount
                        riskScore
                        decision
                        explanation
                    }
                }
            }""",
            {
                "reportId": report_id,
                "transactionId": transaction_id,
                "decision": decision,
            },
        )
        return jsonify(data.get("updateTransactionDecision") or {})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── run ──────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
