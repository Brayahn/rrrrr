import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate, add_years


# =============================================================================
# AUTHENTICATION APIs
# =============================================================================

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    """
    Handle login to ERPNext.

    Args:
        usr: Username or email
        pwd: Password

    Returns:
        dict: Login response with user info and session details

    Example:
        POST /api/method/education_custom.api.login
        {
            "usr": "user@example.com",
            "pwd": "password123"
        }
    """
    try:
        # Validate inputs
        if not usr or not pwd:
            frappe.throw(_("Username and password are required"), frappe.AuthenticationError)

        # Attempt login using Frappe's login manager
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        # Get user details
        user = frappe.get_doc("User", frappe.session.user)

        # Get user roles
        roles = frappe.get_roles(frappe.session.user)

        # Generate API keys if not exist (for subsequent API calls)
        api_key = user.api_key
        api_secret = None
        if not api_key:
            api_key = frappe.generate_hash(length=15)
            user.api_key = api_key
            user.save(ignore_permissions=True)

        # Get the api_secret (only shown once)
        api_secret = user.get_password("api_secret") if user.api_secret else None

        return {
            "success": True,
            "message": _("Login successful"),
            "user": {
                "name": user.name,
                "email": user.email,
                "full_name": user.full_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_image": user.user_image,
                "roles": roles,
            },
            "session": {
                "sid": frappe.session.sid,
                "api_key": api_key,
            }
        }

    except frappe.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["http_status_code"] = 401
        return {
            "success": False,
            "message": _("Invalid username or password")
        }
    except Exception as e:
        frappe.log_error(f"Login error: {str(e)}", "Login API Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An error occurred during login")
        }


@frappe.whitelist(allow_guest=True)
def logout():
    """
    Handle logout from ERPNext.

    Returns:
        dict: Logout confirmation

    Example:
        POST /api/method/education_custom.api.logout
    """
    try:
        frappe.local.login_manager.logout()
        frappe.db.commit()

        return {
            "success": True,
            "message": _("Logged out successfully")
        }
    except Exception as e:
        frappe.log_error(f"Logout error: {str(e)}", "Logout API Error")
        return {
            "success": False,
            "message": _("An error occurred during logout")
        }


@frappe.whitelist(allow_guest=True)
def get_logged_in_user():
    """
    Get the currently logged in user's details.

    Returns:
        dict: Current user info or guest status

    Example:
        GET /api/method/education_custom.api.get_logged_in_user
    """
    if frappe.session.user == "Guest":
        return {
            "logged_in": False,
            "user": "Guest"
        }

    user = frappe.get_doc("User", frappe.session.user)
    roles = frappe.get_roles(frappe.session.user)

    return {
        "logged_in": True,
        "user": {
            "name": user.name,
            "email": user.email,
            "full_name": user.full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_image": user.user_image,
            "roles": roles,
        }
    }


# =============================================================================
# SITE SETUP APIs (Similar to Setup Wizard)
# =============================================================================

@frappe.whitelist(allow_guest=True)
def setup_site(args):
    """
    Set up a new ERPNext site programmatically (similar to Setup Wizard).

    This API handles the complete site setup including:
    - System settings (language, timezone, country, currency)
    - User creation/update
    - Company creation
    - Fiscal year creation
    - Default settings
    - Base fixtures

    Args:
        args (dict or str): Setup configuration containing:
            - language (str): Language code (e.g., "en")
            - country (str): Country name
            - timezone (str): Timezone (e.g., "Africa/Nairobi")
            - currency (str): Currency code (e.g., "KES")
            - full_name (str): Admin user full name
            - email (str): Admin user email
            - password (str, optional): Admin user password
            - company_name (str): Company name
            - company_abbr (str): Company abbreviation (max 10 chars)
            - chart_of_accounts (str, optional): Chart of accounts template
            - fy_start_date (str): Fiscal year start date (YYYY-MM-DD)
            - fy_end_date (str, optional): Fiscal year end date (YYYY-MM-DD)

    Returns:
        dict: Setup result with success status and details

    Example:
        POST /api/method/education_custom.api.setup_site
        {
            "args": {
                "language": "en",
                "country": "Kenya",
                "timezone": "Africa/Nairobi",
                "currency": "KES",
                "full_name": "Admin User",
                "email": "admin@school.edu",
                "password": "securepassword",
                "company_name": "My School",
                "company_abbr": "MS",
                "fy_start_date": "2024-01-01",
                "fy_end_date": "2024-12-31"
            }
        }
    """
    try:
        # Parse args if it's a string
        if isinstance(args, str):
            import json
            args = json.loads(args)

        # Validate required fields
        required_fields = [
            "language", "country", "timezone", "currency",
            "full_name", "email", "company_name", "company_abbr",
            "fy_start_date"
        ]

        missing_fields = [f for f in required_fields if not args.get(f)]
        if missing_fields:
            frappe.throw(
                _("Missing required fields: {0}").format(", ".join(missing_fields)),
                frappe.ValidationError
            )

        # Validate company abbreviation length
        if len(args.get("company_abbr", "")) > 10:
            frappe.throw(_("Company abbreviation must be 10 characters or less"))

        # Sanitize inputs
        args = _sanitize_setup_args(args)

        # Run setup stages
        stages_completed = []

        # Stage 1: Update global/system settings
        _update_system_settings(args)
        stages_completed.append("System settings updated")

        # Stage 2: Create or update user
        _create_or_update_user(args)
        stages_completed.append("User configured")

        # Stage 3: Install base fixtures
        _install_fixtures(args)
        stages_completed.append("Base fixtures installed")

        # Stage 4: Create company
        _create_company(args)
        stages_completed.append("Company created")

        # Stage 5: Create fiscal year
        _create_fiscal_year(args)
        stages_completed.append("Fiscal year created")

        # Stage 6: Set defaults
        _set_defaults(args)
        stages_completed.append("Defaults configured")

        # Mark setup as complete
        frappe.db.set_single_value("System Settings", "setup_complete", 1)
        frappe.db.commit()
        stages_completed.append("Setup marked as complete")

        return {
            "success": True,
            "message": _("Site setup completed successfully"),
            "stages_completed": stages_completed,
            "company": args.get("company_name"),
            "fiscal_year": _get_fiscal_year_name(args)
        }

    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Site setup error: {str(e)}", "Site Setup API Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "success": False,
            "message": _("An error occurred during site setup: {0}").format(str(e))
        }


@frappe.whitelist()
def get_setup_defaults():
    """
    Get default values and options for site setup.

    Returns available languages, countries, timezones, currencies,
    and chart of accounts templates.

    Returns:
        dict: Setup defaults and options

    Example:
        GET /api/method/education_custom.api.get_setup_defaults
    """
    try:
        # Get available languages
        languages = frappe.get_all(
            "Language",
            filters={"enabled": 1},
            fields=["name", "language_name"],
            order_by="language_name"
        )

        # Get countries
        countries = frappe.get_all(
            "Country",
            fields=["name", "code", "time_zones", "date_format"],
            order_by="name"
        )

        # Get currencies
        currencies = frappe.get_all(
            "Currency",
            filters={"enabled": 1},
            fields=["name", "currency_name", "symbol"],
            order_by="name"
        )

        # Get chart of accounts templates
        chart_templates = _get_chart_of_accounts_templates()

        # Get current system settings
        system_settings = frappe.get_single("System Settings")

        return {
            "success": True,
            "defaults": {
                "language": system_settings.language or "en",
                "country": system_settings.country,
                "timezone": system_settings.time_zone,
                "date_format": system_settings.date_format,
                "time_format": system_settings.time_format,
            },
            "options": {
                "languages": languages,
                "countries": countries,
                "currencies": currencies,
                "chart_of_accounts": chart_templates,
            }
        }
    except Exception as e:
        frappe.log_error(f"Get setup defaults error: {str(e)}", "Setup Defaults API Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def check_setup_status():
    """
    Check if the site setup has been completed.

    Returns:
        dict: Setup status and existing configuration

    Example:
        GET /api/method/education_custom.api.check_setup_status
    """
    try:
        setup_complete = cint(frappe.db.get_single_value("System Settings", "setup_complete"))

        # Check for existing company
        companies = frappe.get_all("Company", fields=["name", "abbr", "default_currency"])

        # Check for existing fiscal years
        fiscal_years = frappe.get_all(
            "Fiscal Year",
            fields=["name", "year_start_date", "year_end_date"],
            order_by="year_start_date desc",
            limit=5
        )

        return {
            "success": True,
            "setup_complete": bool(setup_complete),
            "has_company": len(companies) > 0,
            "companies": companies,
            "fiscal_years": fiscal_years,
            "can_run_setup": not setup_complete or len(companies) == 0
        }
    except Exception as e:
        frappe.log_error(f"Check setup status error: {str(e)}", "Setup Status API Error")
        return {
            "success": False,
            "message": str(e)
        }


# =============================================================================
# SETUP HELPER FUNCTIONS
# =============================================================================

def _sanitize_setup_args(args):
    """Sanitize and clean setup arguments."""
    from frappe.utils import strip_html

    sanitized = {}
    for key, value in args.items():
        if isinstance(value, str):
            # Remove HTML tags and strip whitespace
            sanitized[key] = strip_html(value).strip()
        else:
            sanitized[key] = value

    return sanitized


def _update_system_settings(args):
    """Update system-wide settings."""
    settings = frappe.get_single("System Settings")

    settings.language = args.get("language", "en")
    settings.country = args.get("country")
    settings.time_zone = args.get("timezone")

    # Get country-specific settings
    country_doc = frappe.db.get_value(
        "Country",
        args.get("country"),
        ["date_format", "time_zones"],
        as_dict=True
    )

    if country_doc:
        if country_doc.date_format:
            settings.date_format = country_doc.date_format

    settings.save(ignore_permissions=True)

    # Update default currency
    frappe.db.set_default("currency", args.get("currency"))


def _create_or_update_user(args):
    """Create or update the admin user."""
    email = args.get("email")

    if frappe.db.exists("User", email):
        # Update existing user
        user = frappe.get_doc("User", email)
        user.first_name = args.get("full_name", "").split(" ")[0]
        user.last_name = " ".join(args.get("full_name", "").split(" ")[1:]) or None

        if args.get("password"):
            user.new_password = args.get("password")

        user.save(ignore_permissions=True)
    else:
        # Create new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": args.get("full_name", "").split(" ")[0],
            "last_name": " ".join(args.get("full_name", "").split(" ")[1:]) or None,
            "enabled": 1,
            "new_password": args.get("password") or frappe.generate_hash(length=10),
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)

        # Add System Manager role
        user.add_roles("System Manager")


def _install_fixtures(args):
    """Install base fixtures if ERPNext is installed."""
    # Check if ERPNext is installed
    if "erpnext" in frappe.get_installed_apps():
        try:
            from erpnext.setup.setup_wizard.operations.install_fixtures import install
            install(country=args.get("country"))
        except ImportError:
            # ERPNext fixtures not available, skip
            pass
        except Exception as e:
            frappe.log_error(f"Fixture installation error: {str(e)}", "Setup Fixtures Error")


def _create_company(args):
    """Create the company."""
    company_name = args.get("company_name")

    if frappe.db.exists("Company", company_name):
        # Company already exists, update it
        company = frappe.get_doc("Company", company_name)
        company.abbr = args.get("company_abbr")
        company.default_currency = args.get("currency")
        company.country = args.get("country")
        company.save(ignore_permissions=True)
    else:
        # Create new company
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": args.get("company_abbr"),
            "default_currency": args.get("currency"),
            "country": args.get("country"),
            "chart_of_accounts": args.get("chart_of_accounts"),
            "enable_perpetual_inventory": 1
        })
        company.insert(ignore_permissions=True)


def _get_fiscal_year_name(args):
    """Generate fiscal year name."""
    fy_start = getdate(args.get("fy_start_date"))
    fy_end = getdate(args.get("fy_end_date")) if args.get("fy_end_date") else add_years(fy_start, 1) - frappe.utils.datetime.timedelta(days=1)

    if fy_start.year == fy_end.year:
        return str(fy_start.year)
    else:
        return f"{fy_start.year}-{fy_end.year}"


def _create_fiscal_year(args):
    """Create the fiscal year."""
    fy_start = getdate(args.get("fy_start_date"))

    # Calculate fiscal year end if not provided
    if args.get("fy_end_date"):
        fy_end = getdate(args.get("fy_end_date"))
    else:
        # Default to 1 year minus 1 day
        fy_end = add_years(fy_start, 1)
        fy_end = frappe.utils.add_days(fy_end, -1)

    fy_name = _get_fiscal_year_name(args)

    if not frappe.db.exists("Fiscal Year", fy_name):
        fiscal_year = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": fy_name,
            "year_start_date": fy_start,
            "year_end_date": fy_end,
            "is_short_year": 0
        })
        fiscal_year.insert(ignore_permissions=True)

        # Set as default
        frappe.db.set_default("fiscal_year", fy_name)


def _set_defaults(args):
    """Set default settings for the site."""
    company_name = args.get("company_name")

    # Set global defaults
    frappe.db.set_default("company", company_name)
    frappe.db.set_default("country", args.get("country"))
    frappe.db.set_default("currency", args.get("currency"))

    # Create price lists if ERPNext is installed
    if "erpnext" in frappe.get_installed_apps():
        _create_price_lists(args)

        # Update Stock Settings
        if frappe.db.exists("DocType", "Stock Settings"):
            stock_settings = frappe.get_single("Stock Settings")
            stock_settings.stock_uom = "Nos"
            stock_settings.auto_indent = 1
            stock_settings.save(ignore_permissions=True)


def _create_price_lists(args):
    """Create default price lists."""
    currency = args.get("currency")

    # Standard Buying Price List
    if not frappe.db.exists("Price List", "Standard Buying"):
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": "Standard Buying",
            "enabled": 1,
            "buying": 1,
            "selling": 0,
            "currency": currency
        }).insert(ignore_permissions=True)

    # Standard Selling Price List
    if not frappe.db.exists("Price List", "Standard Selling"):
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": "Standard Selling",
            "enabled": 1,
            "buying": 0,
            "selling": 1,
            "currency": currency
        }).insert(ignore_permissions=True)


def _get_chart_of_accounts_templates():
    """Get available chart of accounts templates."""
    templates = []

    if "erpnext" in frappe.get_installed_apps():
        try:
            from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
                get_charts_for_country,
            )

            # Get charts for all countries (use "all" to get generic ones)
            charts = get_charts_for_country("all")
            templates = [{"name": c, "label": c} for c in charts]
        except ImportError:
            pass
        except Exception:
            pass

    if not templates:
        templates = [
            {"name": "Standard", "label": "Standard"},
            {"name": "Standard with Numbers", "label": "Standard with Numbers"}
        ]

    return templates


# =============================================================================
# FEE STRUCTURE APIs
# =============================================================================

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

# =============================================================================
# LMS STUDENT PROGRAMS API
# =============================================================================

@frappe.whitelist()
def get_student_programs(search=None):
    """
    Get enrolled programs for the current student.

    This API returns only programs where the student is enrolled,
    with search functionality by title/name.
    Students cannot self-enroll - enrollment is managed by administrators.

    Args:
        search (str, optional): Search term to filter programs by title/name

    Returns:
        dict: List of enrolled programs with details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your programs"), frappe.AuthenticationError)

    # Get enrolled programs
    enrolled_programs = frappe.get_all(
        "LMS Program Member",
        {"member": frappe.session.user},
        ["parent as name", "progress"]
    )

    programs = []
    for program in enrolled_programs:
        program_details = frappe.db.get_value(
            "LMS Program",
            program.name,
            ["name", "title", "course_count", "member_count"],
            as_dict=True
        )

        if not program_details:
            continue

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            name_match = program_details.name.lower().find(search_lower) >= 0
            title_match = (program_details.title or "").lower().find(search_lower) >= 0
            if not (name_match or title_match):
                continue

        program_details.progress = program.progress
        programs.append(program_details)

    return {
        "success": True,
        "programs": programs
    }


@frappe.validate_and_sanitize_search_inputs
@frappe.whitelist(allow_guest=True)
def get_programs_by_branch(doctype, txt, searchfield, start, page_len, filters):
    """
    Get programs filtered by branch (for Table MultiSelect field).

    The Program doctype has a Table MultiSelect field 'custom_branch'
    which links to a child table containing branch entries.
    """
    branch = filters.get('branch')

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


# =============================================================================
# STUDENT FEES REPORT API
# =============================================================================

@frappe.whitelist()
def get_student_fees_report():
    """
    Get fees report for the currently logged in student.

    Returns paid amount, outstanding balance, and fee details grouped by program.

    Returns:
        dict: Fees summary with total_fees, total_paid, total_outstanding, and details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your fees"), frappe.AuthenticationError)

    # Get the student record linked to this user
    student = frappe.db.get_value("Student", {"user": frappe.session.user}, "name")

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

    # Get fee components for each fee
    for fee in fees:
        fee.components = frappe.get_all(
            "Fee Component",
            filters={"parent": fee.name},
            fields=["fees_category", "description", "amount"],
            order_by="idx"
        )
        # Format dates for display
        fee.posting_date = frappe.utils.formatdate(fee.posting_date)
        fee.due_date = frappe.utils.formatdate(fee.due_date)
        # Determine status
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
