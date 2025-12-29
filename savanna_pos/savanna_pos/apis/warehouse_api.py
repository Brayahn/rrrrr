"""
Warehouse Management API
Handles warehouse creation, management, and staff assignment
"""

import frappe
from frappe import _
from frappe.query_builder import DocType


@frappe.whitelist()
def create_warehouse(
    warehouse_name: str,
    company: str,
    warehouse_type: str = None,
    parent_warehouse: str = None,
    is_group: bool = False,
    is_main_depot: bool = False,
    set_as_default: bool = False,
    account: str = None,
    address_line_1: str = None,
    address_line_2: str = None,
    city: str = None,
    state: str = None,
    pin: str = None,
    phone_no: str = None,
    mobile_no: str = None,
    email_id: str = None,
) -> dict:
    """
    Create a new warehouse.
    
    Warehouse Types:
    - Regional Depot: A regional distribution center
    - Company Warehouse/Shop: Regular warehouse or shop for a company
    - Main Depot: Main depot for a company (optional, one per company recommended)
    
    Args:
        warehouse_name: Name of the warehouse (required)
        company: Company name (required)
        warehouse_type: Type of warehouse - "Regional Depot", "Company Warehouse", "Shop", or "Main Depot" (optional)
        parent_warehouse: Parent warehouse name (optional, for hierarchical structure)
        is_group: Whether this is a group warehouse (default: False)
        is_main_depot: Whether this is the main depot for the company (default: False)
        set_as_default: Whether to set this warehouse as the default warehouse for the company (default: False)
        account: Warehouse account (optional)
        address_line_1: Address line 1 (optional)
        address_line_2: Address line 2 (optional)
        city: City (optional)
        state: State/Province (optional)
        pin: PIN code (optional)
        phone_no: Phone number (optional)
        mobile_no: Mobile number (optional)
        email_id: Email address (optional)
    
    Returns:
        dict: Created warehouse details
    """
    try:
        # Validate company exists
        if not frappe.db.exists("Company", company):
            return {
                "success": False,
                "message": f"Company '{company}' does not exist",
            }
        
        # Check if warehouse already exists
        existing = frappe.db.exists("Warehouse", {"warehouse_name": warehouse_name, "company": company})
        
        if existing:
            return {
                "success": False,
                "message": f"Warehouse '{warehouse_name}' already exists for company '{company}'",
                "name": existing,
            }
        
        # Validate parent warehouse if provided
        if parent_warehouse:
            if not frappe.db.exists("Warehouse", parent_warehouse):
                return {
                    "success": False,
                    "message": f"Parent Warehouse '{parent_warehouse}' does not exist",
                }
            # Verify parent is in same company
            parent_company = frappe.db.get_value("Warehouse", parent_warehouse, "company")
            if parent_company != company:
                return {
                    "success": False,
                    "message": f"Parent Warehouse must belong to the same company",
                }
        
        # Get or create warehouse type if provided
        warehouse_type_name = None
        if warehouse_type:
            warehouse_type_name = get_or_create_warehouse_type(warehouse_type)
            if not warehouse_type_name:
                return {
                    "success": False,
                    "message": f"Failed to create or find warehouse type '{warehouse_type}'",
                }
        
        # Create warehouse
        warehouse = frappe.new_doc("Warehouse")
        warehouse.warehouse_name = warehouse_name
        warehouse.company = company
        warehouse.is_group = 1 if is_group else 0
        
        if warehouse_type_name:
            warehouse.warehouse_type = warehouse_type_name
        
        if parent_warehouse:
            warehouse.parent_warehouse = parent_warehouse
        
        if account:
            warehouse.account = account
        
        # Set address fields
        if address_line_1:
            warehouse.address_line_1 = address_line_1
        if address_line_2:
            warehouse.address_line_2 = address_line_2
        if city:
            warehouse.city = city
        if state:
            warehouse.state = state
        if pin:
            warehouse.pin = pin
        
        # Set contact fields
        if phone_no:
            warehouse.phone_no = phone_no
        if mobile_no:
            warehouse.mobile_no = mobile_no
        if email_id:
            warehouse.email_id = email_id
        
        warehouse.insert(ignore_permissions=False)
        
        # Set main depot flag after insert (if custom field exists)
        if is_main_depot:
            try:
                frappe.db.set_value("Warehouse", warehouse.name, "custom_is_main_depot", 1)
                frappe.db.commit()
            except Exception:
                # Custom field may not exist, continue without it
                pass
        
        # Set as default warehouse for company if requested
        default_set = False
        if set_as_default:
            default_set = set_default_warehouse_for_company(company, warehouse.name)
        
        return {
            "success": True,
            "message": "Warehouse created successfully",
            "name": warehouse.name,
            "warehouse_name": warehouse.warehouse_name,
            "company": warehouse.company,
            "warehouse_type": warehouse.warehouse_type,
            "is_group": warehouse.is_group,
            "is_main_depot": is_main_depot,
            "set_as_default": default_set,
            "parent_warehouse": warehouse.parent_warehouse,
        }
    except frappe.PermissionError as e:
        frappe.log_error(f"Permission error creating warehouse: {str(e)}", "Warehouse Creation Permission Error")
        return {
            "success": False,
            "message": f"Permission denied: You do not have permission to create Warehouse documents. Please contact your administrator to grant you the necessary role permissions.",
            "error_type": "permission_error",
            "required_permission": "Warehouse: Create",
        }
    except frappe.exceptions.ValidationError as e:
        frappe.log_error(f"Validation error creating warehouse: {str(e)}", "Warehouse Creation Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error creating warehouse: {str(e)}", "Warehouse Creation Error")
        return {
            "success": False,
            "message": f"Error creating warehouse: {str(e)}",
            "error_type": "general_error",
        }


@frappe.whitelist()
def list_warehouses(
    company: str = None,
    warehouse_type: str = None,
    is_group: bool = None,
    is_main_depot: bool = None,
    parent_warehouse: str = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    Get list of warehouses with optional filters.
    
    Args:
        company: Filter by company (optional)
        warehouse_type: Filter by warehouse type (optional)
        is_group: Filter by is_group flag (optional)
        is_main_depot: Filter by main depot flag (optional)
        parent_warehouse: Filter by parent warehouse (optional)
        limit: Number of records to return (default: 100)
        offset: Offset for pagination (default: 0)
    
    Returns:
        dict: List of warehouses
    """
    try:
        filters = {}
        
        if company:
            filters["company"] = company
        
        if warehouse_type:
            # Get warehouse type name
            wt = frappe.db.get_value("Warehouse Type", {"name": warehouse_type}, "name")
            if wt:
                filters["warehouse_type"] = wt
        
        if is_group is not None:
            filters["is_group"] = 1 if is_group else 0
        
        if parent_warehouse:
            filters["parent_warehouse"] = parent_warehouse
        
        warehouses = frappe.get_all(
            "Warehouse",
            filters=filters,
            fields=[
                "name",
                "warehouse_name",
                "company",
                "warehouse_type",
                "is_group",
                "parent_warehouse",
                "disabled",
                "address_line_1",
                "city",
                "state",
            ],
            limit=limit,
            start=offset,
            order_by="warehouse_name",
        )
        
        # Add main depot flag if custom field exists and check if warehouse is default
        # Group warehouses by company to efficiently get default warehouses
        companies = set(w["company"] for w in warehouses if w.get("company"))
        default_warehouses_by_company = {}
        
        for comp in companies:
            default_warehouse = get_default_warehouse_for_company(comp)
            if default_warehouse:
                default_warehouses_by_company[comp] = default_warehouse
        
        for warehouse in warehouses:
            try:
                is_main = frappe.db.get_value("Warehouse", warehouse.name, "custom_is_main_depot") or 0
                warehouse["is_main_depot"] = bool(is_main)
            except Exception:
                warehouse["is_main_depot"] = False
            
            # Check if this warehouse is the default for its company
            warehouse_company = warehouse.get("company")
            if warehouse_company and warehouse_company in default_warehouses_by_company:
                warehouse["is_default"] = default_warehouses_by_company[warehouse_company] == warehouse["name"]
            else:
                warehouse["is_default"] = False
        
        # Filter by main depot if requested
        if is_main_depot is not None:
            warehouses = [w for w in warehouses if w.get("is_main_depot") == is_main_depot]
        
        return {
            "success": True,
            "data": warehouses,
            "count": len(warehouses),
        }
    except Exception as e:
        frappe.log_error(f"Error listing warehouses: {str(e)}", "List Warehouses Error")
        return {
            "success": False,
            "message": f"Error listing warehouses: {str(e)}",
        }


@frappe.whitelist()
def get_warehouse_details(name: str) -> dict:
    """
    Get detailed information about a specific warehouse.
    
    Args:
        name: Warehouse name/ID
    
    Returns:
        dict: Warehouse details
    """
    try:
        warehouse = frappe.get_doc("Warehouse", name)
        
        # Get main depot flag (if custom field exists)
        try:
            is_main_depot = frappe.db.get_value("Warehouse", name, "custom_is_main_depot") or 0
        except Exception:
            is_main_depot = 0
        
        # Get warehouse type description if exists
        warehouse_type_desc = None
        if warehouse.warehouse_type:
            warehouse_type_desc = frappe.db.get_value("Warehouse Type", warehouse.warehouse_type, "description")
        
        return {
            "success": True,
            "data": {
                "name": warehouse.name,
                "warehouse_name": warehouse.warehouse_name,
                "company": warehouse.company,
                "warehouse_type": warehouse.warehouse_type,
                "warehouse_type_description": warehouse_type_desc,
                "is_group": warehouse.is_group,
                "is_main_depot": bool(is_main_depot),
                "parent_warehouse": warehouse.parent_warehouse,
                "account": warehouse.account,
                "disabled": warehouse.disabled,
                "address_line_1": warehouse.address_line_1,
                "address_line_2": warehouse.address_line_2,
                "city": warehouse.city,
                "state": warehouse.state,
                "pin": warehouse.pin,
                "phone_no": warehouse.phone_no,
                "mobile_no": warehouse.mobile_no,
                "email_id": warehouse.email_id,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching warehouse details: {str(e)}",
        }


@frappe.whitelist()
def update_warehouse(
    name: str,
    warehouse_name: str = None,
    warehouse_type: str = None,
    parent_warehouse: str = None,
    is_group: bool = None,
    is_main_depot: bool = None,
    account: str = None,
    disabled: bool = None,
    address_line_1: str = None,
    address_line_2: str = None,
    city: str = None,
    state: str = None,
    pin: str = None,
    phone_no: str = None,
    mobile_no: str = None,
    email_id: str = None,
) -> dict:
    """
    Update an existing warehouse.
    
    Args:
        name: Warehouse name/ID
        warehouse_name: Updated warehouse name (optional)
        warehouse_type: Updated warehouse type (optional)
        parent_warehouse: Updated parent warehouse (optional)
        is_group: Update is_group flag (optional)
        is_main_depot: Update main depot flag (optional)
        account: Updated account (optional)
        disabled: Update disabled status (optional)
        address_line_1: Updated address line 1 (optional)
        address_line_2: Updated address line 2 (optional)
        city: Updated city (optional)
        state: Updated state (optional)
        pin: Updated PIN (optional)
        phone_no: Updated phone number (optional)
        mobile_no: Updated mobile number (optional)
        email_id: Updated email (optional)
    
    Returns:
        dict: Update result
    """
    try:
        warehouse = frappe.get_doc("Warehouse", name)
        
        if warehouse_name:
            warehouse.warehouse_name = warehouse_name
        if warehouse_type is not None:
            warehouse_type_name = get_or_create_warehouse_type(warehouse_type)
            if warehouse_type_name:
                warehouse.warehouse_type = warehouse_type_name
        if parent_warehouse is not None:
            if parent_warehouse and not frappe.db.exists("Warehouse", parent_warehouse):
                return {
                    "success": False,
                    "message": f"Parent Warehouse '{parent_warehouse}' does not exist",
                }
            warehouse.parent_warehouse = parent_warehouse
        if is_group is not None:
            warehouse.is_group = 1 if is_group else 0
        if account is not None:
            warehouse.account = account
        if disabled is not None:
            warehouse.disabled = 1 if disabled else 0
        
        # Update address fields
        if address_line_1 is not None:
            warehouse.address_line_1 = address_line_1
        if address_line_2 is not None:
            warehouse.address_line_2 = address_line_2
        if city is not None:
            warehouse.city = city
        if state is not None:
            warehouse.state = state
        if pin is not None:
            warehouse.pin = pin
        
        # Update contact fields
        if phone_no is not None:
            warehouse.phone_no = phone_no
        if mobile_no is not None:
            warehouse.mobile_no = mobile_no
        if email_id is not None:
            warehouse.email_id = email_id
        
        warehouse.save(ignore_permissions=False)
        
        # Update main depot flag (if custom field exists)
        if is_main_depot is not None:
            try:
                frappe.db.set_value("Warehouse", name, "custom_is_main_depot", 1 if is_main_depot else 0)
            except Exception:
                # Custom field may not exist, continue without it
                pass
        
        return {
            "success": True,
            "message": "Warehouse updated successfully",
            "name": warehouse.name,
        }
    except frappe.PermissionError as e:
        frappe.log_error(f"Permission error updating warehouse: {str(e)}", "Warehouse Update Permission Error")
        return {
            "success": False,
            "message": f"Permission denied: You do not have permission to update Warehouse documents. Please contact your administrator to grant you the necessary role permissions.",
            "error_type": "permission_error",
            "required_permission": "Warehouse: Write",
        }
    except frappe.exceptions.ValidationError as e:
        frappe.log_error(f"Validation error updating warehouse: {str(e)}", "Warehouse Update Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error updating warehouse: {str(e)}", "Warehouse Update Error")
        return {
            "success": False,
            "message": f"Error updating warehouse: {str(e)}",
            "error_type": "general_error",
        }


@frappe.whitelist()
def assign_warehouses_to_staff(
    user_email: str,
    warehouses: list,
    replace_existing: bool = True,
) -> dict:
    """
    Assign warehouses to a staff member.
    This restricts the staff member's access to only the assigned warehouses.
    
    Args:
        user_email: Staff user email
        warehouses: List of warehouse names/IDs to assign
        replace_existing: Whether to replace existing assignments (default: True)
    
    Returns:
        dict: Assignment result
    """
    try:
        # Validate user exists
        if not frappe.db.exists("User", user_email):
            return {
                "success": False,
                "message": f"User '{user_email}' does not exist",
            }
        
        # Validate warehouses exist
        invalid_warehouses = []
        valid_warehouses = []
        for warehouse in warehouses:
            if frappe.db.exists("Warehouse", warehouse):
                valid_warehouses.append(warehouse)
            else:
                invalid_warehouses.append(warehouse)
        
        if invalid_warehouses:
            return {
                "success": False,
                "message": f"The following warehouses do not exist: {', '.join(invalid_warehouses)}",
            }
        
        if not valid_warehouses:
            return {
                "success": False,
                "message": "No valid warehouses provided",
            }
        
        # Remove existing warehouse permissions if replacing
        if replace_existing:
            existing_perms = frappe.get_all(
                "User Permission",
                filters={
                    "user": user_email,
                    "allow": "Warehouse",
                },
                fields=["name"],
            )
            for perm in existing_perms:
                frappe.delete_doc("User Permission", perm.name, ignore_permissions=True)
        
        # Create new user permissions for each warehouse
        created_permissions = []
        for warehouse in valid_warehouses:
            # Check if permission already exists
            existing = frappe.db.exists(
                "User Permission",
                {
                    "user": user_email,
                    "allow": "Warehouse",
                    "for_value": warehouse,
                },
            )
            
            if not existing:
                perm = frappe.new_doc("User Permission")
                perm.user = user_email
                perm.allow = "Warehouse"
                perm.for_value = warehouse
                perm.apply_to_all_doctypes = 0
                perm.insert(ignore_permissions=True)
                created_permissions.append(warehouse)
            else:
                created_permissions.append(warehouse)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully assigned {len(created_permissions)} warehouse(s) to user",
            "user": user_email,
            "warehouses": created_permissions,
            "count": len(created_permissions),
        }
    except Exception as e:
        frappe.log_error(f"Error assigning warehouses to staff: {str(e)}", "Assign Warehouses Error")
        return {
            "success": False,
            "message": f"Error assigning warehouses to staff: {str(e)}",
        }


@frappe.whitelist()
def get_staff_warehouses(user_email: str = None) -> dict:
    """
    Get list of warehouses assigned to a staff member.
    If user_email is not provided, returns warehouses for current user.
    
    Args:
        user_email: Staff user email (optional, defaults to current user)
    
    Returns:
        dict: List of assigned warehouses
    """
    try:
        if not user_email:
            user_email = frappe.session.user
        
        if not frappe.db.exists("User", user_email):
            return {
                "success": False,
                "message": f"User '{user_email}' does not exist",
            }
        
        # Get user permissions for warehouses
        permissions = frappe.get_all(
            "User Permission",
            filters={
                "user": user_email,
                "allow": "Warehouse",
            },
            fields=["for_value"],
        )
        
        warehouse_names = [p.for_value for p in permissions]
        
        if not warehouse_names:
            return {
                "success": True,
                "data": [],
                "count": 0,
                "message": "No warehouses assigned to this user. User has access to all warehouses.",
            }
        
        # Get warehouse details
        warehouses = frappe.get_all(
            "Warehouse",
            filters={"name": ["in", warehouse_names]},
            fields=[
                "name",
                "warehouse_name",
                "company",
                "warehouse_type",
                "is_group",
                "parent_warehouse",
                "disabled",
            ],
            order_by="warehouse_name",
        )
        
        # Add main depot flag (if custom field exists)
        for warehouse in warehouses:
            try:
                is_main = frappe.db.get_value("Warehouse", warehouse.name, "custom_is_main_depot") or 0
                warehouse["is_main_depot"] = bool(is_main)
            except Exception:
                warehouse["is_main_depot"] = False
        
        return {
            "success": True,
            "data": warehouses,
            "count": len(warehouses),
            "user": user_email,
        }
    except Exception as e:
        frappe.log_error(f"Error getting staff warehouses: {str(e)}", "Get Staff Warehouses Error")
        return {
            "success": False,
            "message": f"Error getting staff warehouses: {str(e)}",
        }


@frappe.whitelist()
def get_warehouse_staff(warehouse: str) -> dict:
    """
    Get list of staff members assigned to a specific warehouse.
    
    Args:
        warehouse: Warehouse name/ID
    
    Returns:
        dict: List of assigned staff members
    """
    try:
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Get user permissions for this warehouse
        permissions = frappe.get_all(
            "User Permission",
            filters={
                "allow": "Warehouse",
                "for_value": warehouse,
            },
            fields=["user"],
        )
        
        user_emails = [p.user for p in permissions]
        
        if not user_emails:
            return {
                "success": True,
                "data": [],
                "count": 0,
                "message": "No staff members assigned to this warehouse",
            }
        
        # Get user details
        users = frappe.get_all(
            "User",
            filters={"name": ["in", user_emails]},
            fields=[
                "name",
                "email",
                "first_name",
                "last_name",
                "full_name",
                "enabled",
            ],
            order_by="full_name",
        )
        
        return {
            "success": True,
            "data": users,
            "count": len(users),
            "warehouse": warehouse,
        }
    except Exception as e:
        frappe.log_error(f"Error getting warehouse staff: {str(e)}", "Get Warehouse Staff Error")
        return {
            "success": False,
            "message": f"Error getting warehouse staff: {str(e)}",
        }


@frappe.whitelist()
def remove_warehouse_from_staff(
    user_email: str,
    warehouse: str,
) -> dict:
    """
    Remove a warehouse assignment from a staff member.
    
    Args:
        user_email: Staff user email
        warehouse: Warehouse name/ID to remove
    
    Returns:
        dict: Removal result
    """
    try:
        # Find and delete the user permission
        permission = frappe.db.exists(
            "User Permission",
            {
                "user": user_email,
                "allow": "Warehouse",
                "for_value": warehouse,
            },
        )
        
        if not permission:
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' is not assigned to user '{user_email}'",
            }
        
        frappe.delete_doc("User Permission", permission, ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully removed warehouse '{warehouse}' from user '{user_email}'",
        }
    except Exception as e:
        frappe.log_error(f"Error removing warehouse from staff: {str(e)}", "Remove Warehouse Error")
        return {
            "success": False,
            "message": f"Error removing warehouse from staff: {str(e)}",
        }


def get_or_create_warehouse_type(warehouse_type_name: str) -> str:
    """
    Get or create a warehouse type.
    
    Args:
        warehouse_type_name: Name of the warehouse type
    
    Returns:
        str: Warehouse type name/ID
    """
    try:
        # Check if warehouse type exists
        existing = frappe.db.exists("Warehouse Type", warehouse_type_name)
        
        if existing:
            return existing
        
        # Create new warehouse type
        wt = frappe.new_doc("Warehouse Type")
        wt.name = warehouse_type_name
        wt.description = f"Warehouse type: {warehouse_type_name}"
        wt.insert(ignore_permissions=True)
        
        return wt.name
    except Exception as e:
        frappe.log_error(f"Error creating warehouse type: {str(e)}", "Create Warehouse Type Error")
        return None


@frappe.whitelist()
def list_warehouse_types() -> dict:
    """
    Get list of all warehouse types.
    
    Returns:
        dict: List of warehouse types
    """
    try:
        warehouse_types = frappe.get_all(
            "Warehouse Type",
            fields=["name", "description"],
            order_by="name",
        )
        
        return {
            "success": True,
            "data": warehouse_types,
            "count": len(warehouse_types),
        }
    except Exception as e:
        frappe.log_error(f"Error listing warehouse types: {str(e)}", "List Warehouse Types Error")
        return {
            "success": False,
            "message": f"Error listing warehouse types: {str(e)}",
        }


def get_default_warehouse_for_company(company: str) -> str:
    """
    Get default warehouse for a company (helper function).
    Tries both standard and custom field approaches.
    
    Args:
        company: Company name
    
    Returns:
        str: Default warehouse name/ID or None if not set
    """
    try:
        if not frappe.db.exists("Company", company):
            return None
        
        # Try to get default_warehouse from standard field
        default_warehouse = None
        try:
            company_doc = frappe.get_doc("Company", company)
            if hasattr(company_doc, "default_warehouse"):
                default_warehouse = company_doc.default_warehouse
        except Exception:
            pass
        
        # Try custom field if standard field doesn't exist or is None
        if not default_warehouse:
            try:
                default_warehouse = frappe.db.get_value("Company", company, "custom_default_warehouse")
            except Exception:
                pass
        
        return default_warehouse
    except Exception:
        return None


def set_default_warehouse_for_company(company: str, warehouse: str) -> bool:
    """
    Set default warehouse for a company.
    Tries both standard and custom field approaches.
    
    Args:
        company: Company name
        warehouse: Warehouse name/ID
    
    Returns:
        bool: True if successfully set, False otherwise
    """
    try:
        # Validate company exists
        if not frappe.db.exists("Company", company):
            frappe.log_error(f"Company '{company}' does not exist", "Set Default Warehouse Error")
            return False
        
        # Validate warehouse exists and belongs to company
        if not frappe.db.exists("Warehouse", warehouse):
            frappe.log_error(f"Warehouse '{warehouse}' does not exist", "Set Default Warehouse Error")
            return False
        
        warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
        if warehouse_company != company:
            frappe.log_error(
                f"Warehouse '{warehouse}' does not belong to company '{company}'",
                "Set Default Warehouse Error"
            )
            return False
        
        # Try to set default_warehouse field (standard or custom)
        try:
            # First try standard field
            company_doc = frappe.get_doc("Company", company)
            if hasattr(company_doc, "default_warehouse"):
                frappe.db.set_value("Company", company, "default_warehouse", warehouse)
                frappe.db.commit()
                return True
        except Exception:
            pass
        
        # Try custom field
        try:
            frappe.db.set_value("Company", company, "custom_default_warehouse", warehouse)
            frappe.db.commit()
            return True
        except Exception:
            pass
        
        # If both fail, try to add it as a custom field dynamically
        try:
            # Check if custom field exists, if not create it
            custom_field = frappe.db.exists("Custom Field", {
                "dt": "Company",
                "fieldname": "custom_default_warehouse"
            })
            
            if not custom_field:
                # Create custom field
                cf = frappe.new_doc("Custom Field")
                cf.dt = "Company"
                cf.fieldname = "custom_default_warehouse"
                cf.label = "Default Warehouse"
                cf.fieldtype = "Link"
                cf.options = "Warehouse"
                cf.insert(ignore_permissions=True)
                frappe.db.commit()
            
            # Now set the value
            frappe.db.set_value("Company", company, "custom_default_warehouse", warehouse)
            frappe.db.commit()
            return True
        except Exception as e:
            frappe.log_error(
                f"Error setting default warehouse: {str(e)}",
                "Set Default Warehouse Error"
            )
            return False
    except Exception as e:
        frappe.log_error(f"Error setting default warehouse: {str(e)}", "Set Default Warehouse Error")
        return False


@frappe.whitelist()
def set_default_warehouse(company: str, warehouse: str) -> dict:
    """
    Set default warehouse for a company.
    
    Args:
        company: Company name
        warehouse: Warehouse name/ID to set as default
    
    Returns:
        dict: Operation result
    """
    try:
        if not frappe.db.exists("Company", company):
            return {
                "success": False,
                "message": f"Company '{company}' does not exist",
            }
        
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Validate warehouse belongs to company
        warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
        if warehouse_company != company:
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not belong to company '{company}'",
            }
        
        success = set_default_warehouse_for_company(company, warehouse)
        
        if success:
            return {
                "success": True,
                "message": f"Default warehouse set successfully for company '{company}'",
                "company": company,
                "warehouse": warehouse,
            }
        else:
            return {
                "success": False,
                "message": "Failed to set default warehouse. The field may not exist on Company doctype.",
            }
    except Exception as e:
        frappe.log_error(f"Error setting default warehouse: {str(e)}", "Set Default Warehouse API Error")
        return {
            "success": False,
            "message": f"Error setting default warehouse: {str(e)}",
        }


@frappe.whitelist()
def get_default_warehouse(company: str) -> dict:
    """
    Get default warehouse for a company.
    
    Args:
        company: Company name
    
    Returns:
        dict: Default warehouse details or None
    """
    try:
        if not frappe.db.exists("Company", company):
            return {
                "success": False,
                "message": f"Company '{company}' does not exist",
            }
        
        # Get default warehouse using helper function
        default_warehouse = get_default_warehouse_for_company(company)
        
        if not default_warehouse:
            return {
                "success": True,
                "data": None,
                "message": f"No default warehouse set for company '{company}'",
            }
        
        # Get warehouse details
        warehouse = frappe.get_doc("Warehouse", default_warehouse)
        
        return {
            "success": True,
            "data": {
                "name": warehouse.name,
                "warehouse_name": warehouse.warehouse_name,
                "company": warehouse.company,
                "warehouse_type": warehouse.warehouse_type,
                "is_group": warehouse.is_group,
                "parent_warehouse": warehouse.parent_warehouse,
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting default warehouse: {str(e)}", "Get Default Warehouse API Error")
        return {
            "success": False,
            "message": f"Error getting default warehouse: {str(e)}",
        }

