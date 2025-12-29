__version__ = "0.0.1"

import frappe


@frappe.whitelist(allow_guest=True)
def get_fee_structure_details(fee_structure_name):
    """
    Get fee structure details for public display.
    This endpoint is accessible without login for the admissions page.
    """
    if not fee_structure_name:
        return None

    try:
        fs = frappe.get_doc('Fee Structure', fee_structure_name)

        # Only return submitted fee structures
        if fs.docstatus != 1:
            return None

        return {
            'name': fs.name,
            'program': fs.program,
            'academic_year': fs.academic_year,
            'total_amount': fs.total_amount,
            'components': [
                {
                    'fees_category': c.fees_category,
                    'description': c.description or '',
                    'amount': c.amount
                }
                for c in fs.components
            ]
        }
    except frappe.DoesNotExistError:
        return None
    except frappe.PermissionError:
        # Return basic info even if user doesn't have full permission
        fs_data = frappe.db.get_value(
            'Fee Structure',
            fee_structure_name,
            ['name', 'program', 'academic_year', 'total_amount', 'docstatus'],
            as_dict=True
        )
        if fs_data and fs_data.docstatus == 1:
            # Get components via SQL to bypass permission
            components = frappe.db.sql("""
                SELECT fees_category, description, amount
                FROM `tabFee Component`
                WHERE parent = %s
                ORDER BY idx
            """, fee_structure_name, as_dict=True)

            return {
                'name': fs_data.name,
                'program': fs_data.program,
                'academic_year': fs_data.academic_year,
                'total_amount': fs_data.total_amount,
                'components': components
            }
        return None


@frappe.whitelist(allow_guest=True)
def get_fee_structure_for_program(program, academic_year):
    """
    Get fee structure for a specific program and academic year.
    Returns fee structure details dict or None if not found.
    Accessible by guests for the web form.
    """
    if not program or not academic_year:
        return None

    try:
        # Find submitted fee structure for this program and academic year
        fee_structure = frappe.db.sql("""
            SELECT name
            FROM `tabFee Structure`
            WHERE program = %s AND academic_year = %s AND docstatus = 1
            LIMIT 1
        """, (program, academic_year), as_dict=True)

        if not fee_structure:
            return None

        # Get the full details using the existing function
        return get_fee_structure_details(fee_structure[0].name)

    except Exception:
        return None


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_programs_by_branch(doctype, txt, searchfield, start, page_len, filters):
    """
    Get programs filtered by branch (for search link query).

    The Program doctype has a Table MultiSelect field 'custom_branch'
    which links to a child table containing branch entries.
    """
    branch = filters.get('branch') if filters else None

    if not branch:
        # Return all programs if no branch filter
        return frappe.db.sql("""
            SELECT name, program_name
            FROM `tabProgram`
            WHERE (name LIKE %(txt)s OR program_name LIKE %(txt)s)
            ORDER BY program_name
            LIMIT %(start)s, %(page_len)s
        """, {
            'txt': f'%{txt}%',
            'start': start,
            'page_len': page_len
        })

    # Filter programs where the child table contains the selected branch
    return frappe.db.sql("""
        SELECT DISTINCT p.name, p.program_name
        FROM `tabProgram` p
        INNER JOIN `tabBranches` pb ON pb.parent = p.name
        WHERE pb.branch = %(branch)s
        AND pb.parenttype = 'Program'
        AND pb.parentfield = 'custom_branch'
        AND (p.name LIKE %(txt)s OR p.program_name LIKE %(txt)s)
        ORDER BY p.program_name
        LIMIT %(start)s, %(page_len)s
    """, {
        'branch': branch,
        'txt': f'%{txt}%',
        'start': start,
        'page_len': page_len
    })
