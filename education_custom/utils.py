import frappe


def get_fee_structure_details(fee_structure_name):
    """
    Jinja method to get fee structure details for display in web view.
    Returns a dict with total_amount and components list.
    Works for guest users by using SQL queries to bypass permission checks.
    """
    if not fee_structure_name:
        return None

    try:
        # Use SQL to bypass permission checks for guest users
        fs_data = frappe.db.sql("""
            SELECT name, program, academic_year, total_amount, docstatus
            FROM `tabFee Structure`
            WHERE name = %s AND docstatus = 1
        """, fee_structure_name, as_dict=True)

        if not fs_data:
            return None

        fs = fs_data[0]

        # Get components
        components = frappe.db.sql("""
            SELECT fees_category, description, amount
            FROM `tabFee Component`
            WHERE parent = %s
            ORDER BY idx
        """, fee_structure_name, as_dict=True)

        return {
            'name': fs.name,
            'program': fs.program,
            'academic_year': fs.academic_year,
            'total_amount': fs.total_amount,
            'components': [
                {
                    'fees_category': c.fees_category,
                    'category': c.fees_category,  # alias for compatibility
                    'description': c.description or '',
                    'amount': c.amount
                }
                for c in components
            ]
        }
    except Exception:
        return None


def get_fee_structure_for_program(program, academic_year):
    """
    Jinja method to get fee structure for a program and academic year.
    Returns fee structure details dict or None if not found.
    Works for guest users by using SQL queries.
    """
    if not program or not academic_year:
        return None

    try:
        # Use SQL to bypass permission checks for guest users
        fee_structure = frappe.db.sql("""
            SELECT name
            FROM `tabFee Structure`
            WHERE program = %s AND academic_year = %s AND docstatus = 1
            LIMIT 1
        """, (program, academic_year), as_dict=True)

        if fee_structure:
            return get_fee_structure_details(fee_structure[0].name)
    except Exception:
        pass
    return None



def get_fee_structure_for_student_admission(student_admission, program):
    """
    Returns fee structure details for a given Student Admission + Program.
    Safe for guest users (uses SQL).
    """

    if not student_admission or not program:
        return None

    try:
        # 1️⃣ Get academic year from Student Admission (parent)
        admission = frappe.db.sql("""
            SELECT academic_year
            FROM `tabStudent Admission`
            WHERE name = %s
              AND published = 1
        """, (student_admission,), as_dict=True)

        if not admission:
            return None

        academic_year = admission[0].academic_year

        # 2️⃣ Ensure program is allowed in this admission (child table)
        allowed = frappe.db.sql("""
            SELECT program
            FROM `tabStudent Admission Program`
            WHERE parent = %s
              AND parenttype = 'Student Admission'
              AND program = %s
        """, (student_admission, program))

        if not allowed:
            return None

        # 3️⃣ Find active Fee Structure
        fee_structure = frappe.db.sql("""
            SELECT name
            FROM `tabFee Structure`
            WHERE program = %s
              AND academic_year = %s
              AND docstatus = 1
            ORDER BY modified DESC
            LIMIT 1
        """, (program, academic_year), as_dict=True)

        if not fee_structure:
            return None

        # 4️⃣ Return full details
        return get_fee_structure_details(fee_structure[0].name)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "get_fee_structure_for_student_admission"
        )

    return None


# Jinja methods to be registered in hooks.py
jinja_methods = [
    "education_custom.utils.get_fee_structure_details",
    "education_custom.utils.get_fee_structure_for_program",
    "education_custom.utils.get_fee_structure_for_student_admission"
]