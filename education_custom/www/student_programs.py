import frappe

def get_context(context):
    """Context for student programs page."""
    # Require login
    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login to view your programs"), frappe.AuthenticationError)

    context.no_cache = 1
    context.title = "My Programs"

    return context
