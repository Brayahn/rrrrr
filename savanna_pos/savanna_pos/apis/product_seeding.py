
"""
Product Seeding API
Handles POS industry Product seeding for selected industry and general item creation
"""

import frappe
import json
import os
from frappe import _
from frappe.utils import flt
from typing import Dict, List, Optional


@frappe.whitelist(allow_guest=True)
def get_pos_industries(is_active: bool = True) -> Dict:
    """Get list of all POS industries
    
    Args:
        is_active: Filter by active status (default: True)
        
    Returns:
        List of POS industries with details
    """
    try:
        filters = {}
        if is_active:
            filters["is_active"] = 1
        
        industries = frappe.get_all(
            "POS Industry",
            filters=filters,
            fields=[
                "name",
                "industry_code",
                "industry_name",
                "description",
                "serving_location",
                "is_active",
                "sort_order"
            ],
            order_by="sort_order asc, industry_name asc"
        )
        
        frappe.local.response["http_status_code"] = 200
        
        return {
            "success": True,
            "industries": industries,
            "count": len(industries),
            "message": _("Industries retrieved successfully")
        }
    except Exception as e:
        frappe.log_error(f"Error getting POS industries: {str(e)}", "Get POS Industries")
        frappe.throw(_("Error retrieving industries: {0}").format(str(e)), frappe.ValidationError)



@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def seed_products(industry):
    """
    Return all items for the given industry, the total count.
    """

    # Validate industry parameter
    if not industry:
        return {"status": "error", "message": _("Industry is required"), "total_products": 0}

    if not frappe.db.exists("POS Industry", industry):
        return {
            "status": "error",
            "message": _("Industry '{0}' does not exist").format(industry),
            "total_products": 0
        }

    templates = frappe.get_all(
        "Industry Product Template",
        filters={"industry": industry},
        fields=["item_code", "item_name"]
    )

    total_products = len(templates)

    if total_products == 0:
        return {
            "status": "error",
            "message": _("No products found for industry '{0}'").format(industry),
            "total_products": 0
        }

    # Format each template
    products = []
    for tpl in templates:
        products.append({
            "sku": tpl.item_code,
            "name": tpl.item_name,
            "status": "available"
        })

    return {
        "status": "success",
        "industry": industry,
        "total_products": total_products,
        "products": products
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def bulk_upload_products():
    """
    Load industry products from JSON file:industry_products.json
    and insert into 'Industry Product Template'
    
    This function reads from the seed data file and creates Industry Product Template
    records for each industry. It handles errors gracefully and provides detailed
    feedback about what was created, skipped, or failed.
    """
    try:
        frappe.get_meta("Industry Product Template")
    except frappe.DoesNotExistError:
        frappe.throw(
            _("DocType 'Industry Product Template' is not installed or is disabled"),
            title=_("Missing DocType")
        )

    # Load seed file safely
    file_path = frappe.get_app_path(
        "savanna_pos",
        "products_seed_data",
        "industry_products.json"
    )

    if not os.path.exists(file_path):
        frappe.throw(
            _("Seed data file not found at {0}").format(file_path),
            title=_("Missing Seed File")
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        frappe.throw(
            _("Invalid JSON in seed data file"),
            title=_("Invalid Seed File")
        )

    if not isinstance(data, dict) or not data:
        frappe.throw(
            _("Seed data file is empty or malformed"),
            title=_("Invalid Seed Data")
        )

    created = 0
    skipped = 0
    failed = 0

    ignored_industries = []
    failed_items = []

    for industry_key, items in data.items():
        if not isinstance(items, list):
            failed += 1
            continue

        # Try to find industry by code (name) first, then by industry_code, then by industry_name for backward compatibility
        industry = frappe.get_all(
            "POS Industry",
            filters={"name": industry_key},
            pluck="name"
        )
        
        # If not found by name, try by industry_code
        if not industry:
            industry = frappe.get_all(
                "POS Industry",
                filters={"industry_code": industry_key},
                pluck="name"
            )
        
        # If still not found, try by industry_name (for backward compatibility with old JSON format)
        if not industry:
            industry = frappe.get_all(
                "POS Industry",
                filters={"industry_name": industry_key},
                pluck="name"
            )

        if not industry:
            ignored_industries.append(industry_key)
            continue

        industry_name_ref = industry[0]

        for item in items:
            try:
                item_code = item.get("item_code")
                item_name = item.get("item_name")
                item_group = item.get("item_group")
                item_uom = item.get("uom")

                if not item_code or not item_name:
                    failed += 1
                    failed_items.append({
                        "industry": industry_key,
                        "item": item,
                        "reason": "Missing item_code or item_name"
                    })
                    continue

                if frappe.db.exists(
                    "Industry Product Template",
                    {
                        "industry": industry_name_ref,
                        "item_code": item_code
                    }
                ):
                    skipped += 1
                    continue

                doc = frappe.get_doc({
                    "doctype": "Industry Product Template",
                    "industry": industry_name_ref,
                    "item_code": item_code,
                    "item_name": item_name,
                    "item_group": item_group,
                    "uom": item_uom
                })

                doc.insert(ignore_permissions=True)
                created += 1

            except frappe.DuplicateEntryError:
                skipped += 1

            except frappe.DoesNotExistError:
                frappe.db.rollback()
                frappe.throw(
                    _("DocType 'Industry Product Template' became unavailable during execution"),
                    title=_("Fatal Error")
                )

            except Exception as e:
                failed += 1
                failed_items.append({
                    "industry": industry_key,
                    "item": item,
                    "error": str(e)
                })

    frappe.db.commit()
    status = "success"

    if failed:
        status = "partial_success"

    if not created and not skipped:
        status = "no_op"

    return {
        "status": status,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "ignored_industries": ignored_industries,
        "failed_items": failed_items,
        "total_processed": created + skipped + failed
    }


@frappe.whitelist(methods=["POST"])
def create_seed_item(company: str = None):
    """
    Create Items, Item Prices, and optionally update inventory from seed data.
    
    This function creates Item master records, Item Price records (selling and/or buying),
    and optionally creates Material Receipt Stock Entry to add inventory quantities.
    All records are scoped to the authenticated user's company.
    
    **Authentication Required**: This endpoint requires user authentication. Items will be scoped to the user's company.
    
    **Item Code Prefixing**: Item codes are automatically prefixed with the company abbreviation (e.g., "ABC-BURG001")
    to ensure uniqueness across different companies. If an item code already starts with the company abbreviation,
    it will be used as-is. This prevents conflicts when multiple companies seed the same product codes.

    Expected JSON payload:
    {
        "price_list": "Standard Selling",  // Required - Selling price list
        "buying_price_list": "Standard Buying",  // Optional - Buying price list
        "company": "Your Company Name",  // Optional - defaults to user's default company
        "industry": "REST",  // Optional - POS Industry code. If not provided, uses user's industry or NULL for global products
        "warehouse": "Main Warehouse",  // Optional - default warehouse for all items
        "items": [
            {
                "item_code": "BURG001",
                "item_name": "Cheese Burger",
                "item_price": 5.99,  // Required - Selling price
                "buying_price": 3.50,  // Optional - Buying/cost price (requires buying_price_list)
                "item_group": "All Item Groups",
                "uom": "Nos",
                "qty": 100,  // Optional - Quantity to add to inventory (requires warehouse)
                "warehouse": "Main Warehouse",  // Optional - Per-item warehouse (overrides default)
                "basic_rate": 3.50  // Optional - Cost per unit for inventory valuation (defaults to buying_price or 0)
            }
        ]
    }
    
    Returns:
        Dictionary with status, created count, skipped count, failed items, stock entries created, and total received
    """
    # Read & parse JSON safely
    payload = {}
    try:
        raw_data = frappe.request.data
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        if raw_data:
            payload = json.loads(raw_data)
    except Exception:
        payload = {}

    if not payload:
        payload = frappe.form_dict or {}

    if not isinstance(payload, dict):
        frappe.throw(_("Invalid payload"))

    # Validate user authentication
    if frappe.session.user == "Guest":
        frappe.throw(
            _("Please log in to create items. Your session has expired or you are not authenticated."),
            frappe.AuthenticationError
        )

    price_list = payload.get("price_list")
    buying_price_list = payload.get("buying_price_list")  # Optional
    items = payload.get("items")
    industry_code = payload.get("industry")  # Optional - industry code from payload
    default_warehouse = payload.get("warehouse")  # Optional - default warehouse for all items
    # Get company from payload or use parameter, fallback to user default
    company = payload.get("company") or company

    if not price_list:
        frappe.throw(_("Price List is required"))

    if not items or not isinstance(items, list):
        frappe.throw(_("Items must be a non-empty list"))
    
    # Validate buying price list if provided
    if buying_price_list:
        if not frappe.db.exists("Price List", buying_price_list):
            frappe.throw(_("Buying Price List '{0}' does not exist").format(buying_price_list))
        # Verify it's a buying price list
        price_list_details = frappe.db.get_value(
            "Price List",
            buying_price_list,
            ["buying", "selling", "enabled"],
            as_dict=True
        )
        if not price_list_details or not price_list_details.get("enabled"):
            frappe.throw(_("Buying Price List '{0}' is disabled or does not exist").format(buying_price_list))
        if not price_list_details.get("buying"):
            frappe.throw(_("Price List '{0}' is not a buying price list").format(buying_price_list))

    for doctype in ("Item", "Item Price"):
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(_("{0} DocType is missing").format(doctype))

    # Get company - from parameter, payload, or user default
    if not company:
        company = frappe.defaults.get_user_default("Company")
        if not company:
            frappe.throw(
                _("Company is required. Please set a default company in your profile settings or provide the company parameter when creating items."),
                frappe.ValidationError
            )

    # Validate company exists
    if not frappe.db.exists("Company", company):
        frappe.throw(
            _("The company '{0}' does not exist. Please check the company name and try again.").format(company),
            frappe.ValidationError
        )

    # Get company abbreviation for item code prefixing
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    if not company_abbr:
        frappe.throw(
            _("Company '{0}' does not have an abbreviation set. Please set the company abbreviation in Company settings.").format(company),
            frappe.ValidationError
        )
    company_abbr = company_abbr.strip().upper()

    # Determine industry for products:
    # 1. Use industry from payload if provided
    # 2. Otherwise use user's industry if available
    # 3. Otherwise NULL (global products available to all industries)
    product_industry = None
    
    if industry_code:
        # Validate industry exists
        industry_doc = frappe.db.get_value(
            "POS Industry",
            {"name": industry_code, "is_active": 1},
            "name"
        )
        if not industry_doc:
            # Try by industry_code field
            industry_doc = frappe.db.get_value(
                "POS Industry",
                {"industry_code": industry_code, "is_active": 1},
                "name"
            )
        if industry_doc:
            product_industry = industry_doc
        else:
            frappe.throw(
                _("The industry '{0}' does not exist or is not active. Please provide a valid industry code.").format(industry_code),
                frappe.ValidationError
            )
    else:
        # Use user's industry if available
        user_industry = frappe.db.get_value("User", frappe.session.user, "custom_pos_industry")
        if user_industry:
            product_industry = user_industry
        # If no user industry, product_industry remains None (global product)

    created = 0
    skipped = 0
    failed = []
    stock_entries_created = 0
    stock_entry_items = []  # Collect items for stock entry if qty is provided

    for row in items:
        try:
            if not isinstance(row, dict):
                raise ValueError(_("Each item must be an object"))

            original_item_code = row.get("item_code")
            item_name = row.get("item_name")
            item_price = flt(row.get("item_price"))
            buying_price = flt(row.get("buying_price")) if row.get("buying_price") is not None else None
            item_group = row.get("item_group") or "All Item Groups"
            item_uom = row.get("uom")
            qty = flt(row.get("qty")) if row.get("qty") is not None else None
            item_warehouse = row.get("warehouse") or default_warehouse
            basic_rate = flt(row.get("basic_rate")) if row.get("basic_rate") is not None else None
            
            if not original_item_code or not item_name:
                raise ValueError(_("Item Code and Item Name are required"))

            # Prefix item code with company abbreviation to ensure uniqueness across companies
            # Format: {ABBR}-{original_code}
            # Only prefix if not already prefixed with this company's abbreviation
            if original_item_code.upper().startswith(f"{company_abbr}-"):
                # Already prefixed with this company's abbreviation, use as-is
                item_code = original_item_code
            else:
                # Add company abbreviation prefix
                item_code = f"{company_abbr}-{original_item_code}"

            if item_price < 0:
                raise ValueError(_("Item Price must be >= 0"))
            
            if buying_price is not None and buying_price < 0:
                raise ValueError(_("Buying Price must be >= 0"))
            
            if buying_price is not None and buying_price > 0 and not buying_price_list:
                raise ValueError(_("Buying Price List is required when providing buying_price"))
            
            if qty is not None:
                if qty <= 0:
                    raise ValueError(_("Quantity must be greater than 0 for item '{0}'").format(original_item_code))
                if not item_warehouse:
                    raise ValueError(_("Warehouse is required when providing qty for item '{0}'").format(original_item_code))

            # Check if item_code exists globally (item_code is PRIMARY KEY, so it must be unique)
            existing_item_global = frappe.db.exists("Item", item_code)
            
            if existing_item_global:
                # Item exists - check which company it belongs to
                existing_company = frappe.db.get_value("Item", item_code, "custom_company")
                
                # If item exists for THIS company, skip it
                if existing_company == company:
                    skipped += 1
                    continue
                else:
                    # Item exists but for a different company (or no company) - can't create due to PRIMARY KEY constraint
                    company_msg = existing_company if existing_company else _("no company (global)")
                    failed.append({
                        "item_code": original_item_code,
                        "prefixed_item_code": item_code,
                        "error": _("Item code '{0}' (prefixed as '{1}') already exists and belongs to company '{2}'. Item codes must be unique globally across all companies.").format(
                            original_item_code, item_code, company_msg
                        )
                    })
                    continue

            # Create Item
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_name,
                "item_group": item_group,
                "stock_uom": item_uom or "Nos",
                "is_stock_item": 1
            })
            
            # Set company for product isolation (multi-tenant)
            item_doc.custom_company = company
            
            # Set POS industry (from payload, user's industry, or NULL for global)
            item_doc.custom_pos_industry = product_industry
            
            # Prevent eTIMS registration by default
            item_doc.custom_prevent_etims_registration = 1
            
            try:
                item_doc.insert(ignore_permissions=True)
            except (frappe.DuplicateEntryError, frappe.UniqueValidationError) as e:
                # Handle duplicate entry errors gracefully (fallback in case check above missed it)
                skipped += 1
                continue
            except Exception as e:
                # Check if it's an IntegrityError (database-level duplicate)
                error_str = str(e)
                if "Duplicate entry" in error_str or "IntegrityError" in error_str or "1062" in error_str:
                    # Item was created between our check and insert - skip it
                    skipped += 1
                    continue
                # Re-raise other exceptions
                raise

            # Create Selling Item Price
            try:
                item_price_doc = frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "uom": item_uom or "Nos",
                    "price_list": price_list,
                    "price_list_rate": item_price
                })
                
                # Set company if Item Price has company field (for multi-tenant isolation)
                if hasattr(item_price_doc, "company"):
                    item_price_doc.company = company
                
                item_price_doc.insert(ignore_permissions=True)
            except (frappe.DuplicateEntryError, frappe.UniqueValidationError) as e:
                # Item Price already exists for this item_code, price_list, and uom - skip silently
                pass
            except Exception as e:
                # Check if it's an IntegrityError (database-level duplicate)
                error_str = str(e)
                if "Duplicate entry" in error_str or "IntegrityError" in error_str or "1062" in error_str:
                    # Item Price already exists - skip silently
                    pass
                else:
                    # Re-raise other exceptions
                    raise
            
            # Create Buying Item Price if buying_price_list and buying_price are provided
            if buying_price_list and buying_price is not None and buying_price > 0:
                try:
                    buying_item_price_doc = frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": item_code,
                        "uom": item_uom or "Nos",
                        "price_list": buying_price_list,
                        "price_list_rate": buying_price
                    })
                    
                    # Set company if Item Price has company field
                    if hasattr(buying_item_price_doc, "company"):
                        buying_item_price_doc.company = company
                    
                    buying_item_price_doc.insert(ignore_permissions=True)
                except (frappe.DuplicateEntryError, frappe.UniqueValidationError) as e:
                    # Item Price already exists for this item_code, price_list, and uom - skip silently
                    pass
                except Exception as e:
                    # Check if it's an IntegrityError (database-level duplicate)
                    error_str = str(e)
                    if "Duplicate entry" in error_str or "IntegrityError" in error_str or "1062" in error_str:
                        # Item Price already exists - skip silently
                        pass
                    else:
                        # Re-raise other exceptions
                        raise
            
            # Collect item for stock entry if qty is provided
            if qty is not None and qty > 0 and item_warehouse:
                # Use basic_rate if provided, otherwise use buying_price, otherwise 0
                valuation_rate = basic_rate if basic_rate is not None and basic_rate > 0 else (buying_price if buying_price is not None and buying_price > 0 else 0)
                
                stock_entry_items.append({
                    "item_code": item_code,
                    "qty": qty,
                    "t_warehouse": item_warehouse,
                    "basic_rate": valuation_rate,
                    "uom": item_uom or "Nos"
                })

            created += 1

        except Exception as e:
            # Get original_item_code if available, otherwise use row.get
            original_code = original_item_code if 'original_item_code' in locals() else row.get("item_code")
            prefixed_code = item_code if 'item_code' in locals() else None
            failed.append({
                "item_code": original_code,
                "prefixed_item_code": prefixed_code,
                "error": str(e)
            })

    # Create Material Receipt Stock Entry if there are items with qty
    stock_entry_name = None
    if stock_entry_items:
        try:
            # Validate warehouses exist
            warehouses_to_check = set()
            for item in stock_entry_items:
                warehouses_to_check.add(item["t_warehouse"])
            
            for warehouse in warehouses_to_check:
                if not frappe.db.exists("Warehouse", warehouse):
                    raise ValueError(_("Warehouse '{0}' does not exist").format(warehouse))
            
            # Create Stock Entry
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = "Material Receipt"
            stock_entry.company = company
            stock_entry.purpose = "Material Receipt"
            
            # Add items to stock entry
            for item in stock_entry_items:
                stock_entry.append("items", {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "t_warehouse": item["t_warehouse"],
                    "basic_rate": item["basic_rate"],
                    "uom": item["uom"],
                    "conversion_factor": 1.0
                })
            
            # Validate and save stock entry
            stock_entry.validate()
            stock_entry.insert(ignore_permissions=True)
            stock_entry.submit()
            stock_entry_name = stock_entry.name
            stock_entries_created = 1
            
        except Exception as e:
            frappe.log_error(
                f"Error creating stock entry for items: {str(e)}",
                "Create Seed Item - Stock Entry Error"
            )
            # Add to failed items but don't fail the entire operation
            failed.append({
                "item_code": "STOCK_ENTRY",
                "error": _("Failed to create stock entry: {0}").format(str(e))
            })

    frappe.db.commit()

    # Response
    return {
        "status": (
            "success"
            if created == len(items) and not failed
            else "partial_success"
            if created > 0
            else "failed"
        ),
        "company": company,
        "company_abbr": company_abbr,
        "industry": product_industry,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "total_received": len(items),
        "stock_entry_created": stock_entries_created > 0,
        "stock_entry_name": stock_entry_name,
        "inventory_items_count": len(stock_entry_items) if stock_entry_items else 0,
        "note": _("Item codes are automatically prefixed with company abbreviation '{0}' to ensure uniqueness across companies. Format: {0}-{{original_code}}").format(company_abbr)
    }
