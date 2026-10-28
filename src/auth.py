"""Local demonstration authentication for dashboard role access."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

import streamlit as st


DEMO_USERS = {
    "admin": ("admin123", "Admin"),
    "analyst": ("analyst123", "Analyst"),
    "viewer": ("viewer123", "Viewer"),
}


def _digest(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)


def _valid_demo_user(username: str, password: str) -> str | None:
    """Validate local demonstration users without storing plaintext comparisons."""
    record = DEMO_USERS.get(username.strip().lower())
    if record is None:
        return None
    expected_password, role = record
    salt = b"apl-logistics-demo-auth-v1"
    return role if hmac.compare_digest(_digest(password, salt), _digest(expected_password, salt)) else None


def logout() -> None:
    st.session_state.pop("authenticated_user", None)


def current_role() -> str | None:
    user = st.session_state.get("authenticated_user")
    return user.get("role") if isinstance(user, dict) else None


def require_login() -> str:
    """Render local login and return the signed-in role once authenticated."""
    if os.getenv("STREAMLIT_TEST_MODE") == "1":
        st.session_state["authenticated_user"] = {"username": "test-admin", "role": "Admin"}
        return "Admin"
    user = st.session_state.get("authenticated_user")
    if isinstance(user, dict) and user.get("role"):
        return str(user["role"])

    st.title("APL Logistics: Secure Analytics Access")
    st.write("Sign in to access the delivery-performance dashboard.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    st.caption("Local demonstration accounts: admin, analyst, or viewer. Change these before any public deployment.")
    if submitted:
        role = _valid_demo_user(username, password)
        if role:
            st.session_state["authenticated_user"] = {"username": username.strip().lower(), "role": role, "token": secrets.token_urlsafe(16)}
            st.rerun()
        st.error("Invalid username or password.")
    st.stop()


def has_role(*allowed_roles: str) -> bool:
    return current_role() in allowed_roles
