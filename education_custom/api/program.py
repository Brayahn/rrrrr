import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_programs_by_branch(branch):
    """
    Returns a list of Programs that have the given branch in their child table 'custom_branch'.
    """
    if not branch:
        return []

    programs = frappe.get_all("Program",
        filters={
            "name": ["in", frappe.get_all("Branches", 
                filters={"branch": branch}, pluck="parent")]
        },
        fields=["name"]
    )
    print('[p.name for p in programs]',[p.name for p in programs])
    return [p.name for p in programs]
