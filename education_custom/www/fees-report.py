import frappe

no_cache = 1

def get_context(context):
    """Context for Fees Report page."""
    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login to view your fees"), frappe.AuthenticationError)

    context.no_cache = 1
    context.show_sidebar = True

    return context
