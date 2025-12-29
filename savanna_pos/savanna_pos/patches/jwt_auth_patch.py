"""
Patch to add JWT token validation to OAuth validation
This ensures JWT tokens are validated before OAuth validation fails
"""

import frappe


def validate_oauth_with_jwt(authorization_header):
    """
    Enhanced OAuth validation that also checks for JWT tokens
    This is a monkey patch of frappe.auth.validate_oauth
    """
    from frappe.integrations.oauth2 import get_oauth_server
    from frappe.oauth import get_url_delimiter
    from urllib.parse import urlparse, urlencode
    
    if authorization_header[0].lower() != "bearer":
        return
    
    form_dict = frappe.local.form_dict
    token = authorization_header[1]
    
    # First, try JWT validation if token looks like a JWT
    if len(token) <= 200:  # JWT tokens are typically shorter
        try:
            # Check if it's not an OAuth token
            if not frappe.db.exists("OAuth Bearer Token", token):
                # Try JWT validation
                from savanna_pos.savanna_pos.apis.auth_api import get_jwt_secret_key
                import jwt
                
                try:
                    jwt_secret_key = get_jwt_secret_key()
                    payload = jwt.decode(token, jwt_secret_key, algorithms=["HS256"])
                    user = payload.get("sub")
                    
                    if user and frappe.db.exists("User", user):
                        if frappe.db.get_value("User", user, "enabled"):
                            frappe.set_user(user)
                            frappe.local.form_dict = form_dict
                            return
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                    # Not a valid JWT, continue with OAuth validation
                    pass
                except Exception:
                    # Other JWT errors, continue with OAuth
                    pass
        except Exception:
            # If JWT check fails, continue with OAuth
            pass
    
    # Continue with standard OAuth validation
    req = frappe.request
    parsed_url = urlparse(req.url)
    access_token = {"access_token": token}
    uri = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
    http_method = req.method
    headers = req.headers
    body = req.get_data()
    if req.content_type and "multipart/form-data" in req.content_type:
        body = None
    
    try:
        required_scopes = frappe.db.get_value("OAuth Bearer Token", token, "scopes").split(
            get_url_delimiter()
        )
        valid, _oauthlib_request = get_oauth_server().verify_request(
            uri, http_method, body, headers, required_scopes
        )
        if valid:
            frappe.set_user(frappe.db.get_value("OAuth Bearer Token", token, "user"))
            frappe.local.form_dict = form_dict
    except AttributeError:
        pass

