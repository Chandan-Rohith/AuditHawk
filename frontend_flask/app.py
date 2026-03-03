"""
AuditHawk – Flask Frontend
Serves Jinja2-rendered pages and proxies auth requests to the Django GraphQL backend.
"""

import os
import json
import requests as http_requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "audithawk-flask-secret-change-me")

# Django backend GraphQL endpoint
GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://localhost:8000/graphql/")



# ── helpers ──────────────────────────────────────────────

def gql(query: str, variables: dict | None = None) -> dict:
    """Send a GraphQL request to the Django backend."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = http_requests.post(
        GRAPHQL_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    data = resp.json()
    if "errors" in data:
        raise Exception(data["errors"][0]["message"])
    return data["data"]


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
@login_required
def main_app():
    user = session.get("user", {})
    return render_template("main.html", user=user)


# ── run ──────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
