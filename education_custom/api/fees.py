import frappe
from frappe import _


@frappe.whitelist()
def get_student_fees_report():
    """
    Get fees report for the currently logged in student.
    Returns paid amount, outstanding balance, and fee details.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your fees"), frappe.AuthenticationError)

    # Try to find student by user field first
    student = frappe.db.get_value("Student", {"user": frappe.session.user}, "name")

    # If not found, try by email
    if not student:
        student = frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")

    if not student:
        return {
            "success": False,
            "message": _("No student record found for your account"),
            "total_fees": 0,
            "total_paid": 0,
            "total_outstanding": 0,
            "fees": []
        }

    # Get student details
    student_doc = frappe.get_doc("Student", student)

    # Get all submitted fees for this student
    fees = frappe.db.sql("""
        SELECT
            f.name,
            f.posting_date,
            f.due_date,
            f.program,
            f.academic_year,
            f.academic_term,
            f.grand_total,
            f.outstanding_amount,
            (f.grand_total - f.outstanding_amount) as paid_amount,
            f.docstatus
        FROM `tabFees` f
        WHERE f.student = %s
        AND f.docstatus = 1
        ORDER BY f.posting_date DESC
    """, student, as_dict=True)

    # Calculate totals
    total_fees = sum(fee.grand_total or 0 for fee in fees)
    total_outstanding = sum(fee.outstanding_amount or 0 for fee in fees)
    total_paid = total_fees - total_outstanding

    # Get fee components and format data
    for fee in fees:
        fee.components = frappe.get_all(
            "Fee Component",
            filters={"parent": fee.name},
            fields=["fees_category", "description", "amount"],
            order_by="idx"
        )
        fee.posting_date = frappe.utils.formatdate(fee.posting_date)
        fee.due_date = frappe.utils.formatdate(fee.due_date)

        if fee.outstanding_amount == 0:
            fee.status = "Paid"
            fee.status_color = "green"
        elif fee.outstanding_amount < fee.grand_total:
            fee.status = "Partially Paid"
            fee.status_color = "orange"
        else:
            fee.status = "Unpaid"
            fee.status_color = "red"

    return {
        "success": True,
        "student_name": student_doc.student_name,
        "student_id": student,
        "total_fees": total_fees,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "fees": fees,
        "currency": frappe.db.get_default("currency") or "KES"
    }
