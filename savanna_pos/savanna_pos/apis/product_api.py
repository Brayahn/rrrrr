"""
Product Management API
Handles complete product/item management including CRUD operations, search, pricing, and stock management
"""

import frappe
from frappe import _
from frappe.query_builder import DocType
from typing import Dict, List, Optional
from frappe.utils import flt, cint, cstr, nowdate, getdate
import json
from datetime import datetime
import erpnext


@frappe.whitelist()
def create_product(
    item_code: str,
    item_name: str,
    item_group: str = "All Item Groups",
    stock_uom: str = "Nos",
    standard_rate: float = 0.0,
    description: str = None,
    is_stock_item: bool = True,
    is_sales_item: bool = True,
    is_purchase_item: bool = False,
    brand: str = None,
    barcode: str = None,
    image: str = None,
    weight_per_unit: float = None,
    weight_uom: str = None,
    item_defaults: List[Dict] = None,
    taxes: List[Dict] = None,
    company: str = None,
    # eTIMS fields (optional - will skip eTIMS validation if not provided)
    prevent_etims_registration: bool = True,
    etims_country_of_origin_code: str = None,
    product_type: str = None,
    packaging_unit_code: str = None,
    unit_of_quantity_code: str = None,
    item_classification: str = None,
    taxation_type: str = None
) -> Dict:
    """Create a new product/item
    
    Args:
        item_code: Unique item code
        item_name: Item name
        item_group: Item group (default: "All Item Groups")
        stock_uom: Stock unit of measure (default: "Nos")
        standard_rate: Standard selling rate
        description: Item description
        is_stock_item: Whether item is a stock item
        is_sales_item: Whether item can be sold
        is_purchase_item: Whether item can be purchased
        brand: Brand name
        barcode: Barcode for the item
        image: Image URL or file path
        weight_per_unit: Weight per unit
        weight_uom: Weight unit of measure
        item_defaults: List of item defaults (warehouse, company, etc.)
        taxes: List of tax templates
        company: Company for item defaults
        prevent_etims_registration: Skip eTIMS validation (default: True). 
            Set to False to enable eTIMS registration, but then all eTIMS fields are required.
        etims_country_of_origin_code: Country of origin code (required if prevent_etims_registration is False)
        product_type: Product type name from "Navari eTims Product Type" doctype (required if prevent_etims_registration is False)
        packaging_unit_code: Packaging unit code (required if prevent_etims_registration is False)
        unit_of_quantity_code: Unit of quantity code (required if prevent_etims_registration is False)
        item_classification: Item classification name (required if prevent_etims_registration is False)
        taxation_type: Taxation type name (required if prevent_etims_registration is False)
        
    Returns:
        Created product details
    """
    try:
        # Validate user permissions
        if frappe.session.user == "Guest":
            frappe.throw(_("Please log in to create a product. Your session has expired or you are not authenticated."), frappe.AuthenticationError)
        
        # Validate required fields
        if not item_code or not item_code.strip():
            frappe.throw(_("Product code is required. Please provide a unique code for this product."), frappe.ValidationError)
        
        if not item_name or not item_name.strip():
            frappe.throw(_("Product name is required. Please provide a name for this product."), frappe.ValidationError)
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                frappe.throw(_("Company is required. Please set a default company in your profile settings or provide the company parameter when creating the product."), frappe.ValidationError)
        
        # Validate company exists
        if not frappe.db.exists("Company", company):
            frappe.throw(_("The company '{0}' does not exist. Please check the company name and try again, or contact your administrator if you believe this is an error.").format(company), frappe.ValidationError)
        
        # Check if item code already exists
        if frappe.db.exists("Item", item_code):
            frappe.throw(_("A product with the code '{0}' already exists. Please use a different product code.").format(item_code), frappe.ValidationError)
        
        # Validate item group
        if not frappe.db.exists("Item Group", item_group):
            frappe.throw(_("The product category '{0}' does not exist. Please select a valid category from the list.").format(item_group), frappe.ValidationError)
        
        # Validate UOM
        if not frappe.db.exists("UOM", stock_uom):
            frappe.throw(_("The unit of measure '{0}' does not exist. Please select a valid unit (e.g., 'Nos', 'Kg', 'Ltr') from the list.").format(stock_uom), frappe.ValidationError)
        
        # Validate brand if provided
        if brand and not frappe.db.exists("Brand", brand):
            frappe.throw(_("The brand '{0}' does not exist. Please select a valid brand from the list or leave this field empty.").format(brand), frappe.ValidationError)
        
        # Validate weight UOM if provided
        if weight_uom and not frappe.db.exists("UOM", weight_uom):
            frappe.throw(_("The weight unit '{0}' does not exist. Please select a valid unit from the list.").format(weight_uom), frappe.ValidationError)
        
        # Validate eTIMS fields if registration is enabled
        if not prevent_etims_registration:
            missing_fields = []
            if not etims_country_of_origin_code:
                missing_fields.append("Country of Origin Code")
            if not product_type:
                missing_fields.append("Product Type")
            if not packaging_unit_code:
                missing_fields.append("Packaging Unit Code")
            if not unit_of_quantity_code:
                missing_fields.append("Unit of Quantity Code")
            if not item_classification:
                missing_fields.append("Item Classification")
            if not taxation_type:
                missing_fields.append("Taxation Type")
            
            if missing_fields:
                frappe.throw(_("To enable eTIMS registration, the following fields are required: {0}. Please provide all required eTIMS information or set prevent_etims_registration to True.").format(", ".join(missing_fields)), frappe.ValidationError)
        
        # Create item
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_name
        item.item_group = item_group
        item.stock_uom = stock_uom
        item.standard_rate = flt(standard_rate)
        item.description = description
        item.is_stock_item = 1 if is_stock_item else 0
        item.is_sales_item = 1 if is_sales_item else 0
        item.is_purchase_item = 1 if is_purchase_item else 0
        
        if brand:
            item.brand = brand
        if image:
            item.image = image
        if weight_per_unit:
            item.weight_per_unit = flt(weight_per_unit)
        if weight_uom:
            item.weight_uom = weight_uom
        
        # Add item defaults
        # Note: We don't set default_price_list here to prevent automatic price creation
        # which would fail due to permissions. We'll create the price manually after insert.
        if item_defaults:
            for default in item_defaults:
                # Remove default_price_list to prevent automatic price creation
                default_copy = default.copy()
                default_copy.pop("default_price_list", None)
                item.append("item_defaults", default_copy)
        else:
            # Add default company warehouse
            default_warehouse = frappe.db.get_value(
                "Warehouse",
                {"company": company, "is_group": 0},
                "name",
                order_by="creation desc"
            )
            if default_warehouse:
                item.append("item_defaults", {
                    "company": company,
                    "default_warehouse": default_warehouse
                })
        
        # Add taxes
        if taxes:
            for tax in taxes:
                item.append("taxes", tax)
        
        # Add barcode
        if barcode:
            item.append("barcodes", {
                "barcode": barcode
            })
        
        # Set company for product isolation
        item.custom_company = company
        
        # Set eTIMS fields or prevent eTIMS registration
        item.custom_prevent_etims_registration = 1 if prevent_etims_registration else 0
        
        if not prevent_etims_registration:
            # Set eTIMS fields if provided
            if etims_country_of_origin_code:
                item.custom_etims_country_of_origin_code = etims_country_of_origin_code
            if product_type:
                item.custom_product_type = product_type
            if packaging_unit_code:
                item.custom_packaging_unit_code = packaging_unit_code
            if unit_of_quantity_code:
                item.custom_unit_of_quantity_code = unit_of_quantity_code
            if item_classification:
                item.custom_item_classification = item_classification
            if taxation_type:
                item.custom_taxation_type = taxation_type
        
        # Temporarily set standard_rate to 0 to prevent automatic price creation
        # We'll restore it and create the price manually after insert
        temp_standard_rate = item.standard_rate
        item.standard_rate = 0
        
        item.insert(ignore_permissions=True)
        
        # Restore standard_rate
        if temp_standard_rate:
            item.standard_rate = temp_standard_rate
            item.db_set("standard_rate", temp_standard_rate)
            
            # Manually create Item Price with ignore_permissions if standard_rate is set
            try:
                # Get default price list
                default_price_list = None
                if item_defaults:
                    for default in item_defaults:
                        if default.get("default_price_list"):
                            default_price_list = default.get("default_price_list")
                            break
                
                if not default_price_list:
                    default_price_list = frappe.get_single_value(
                        "Selling Settings", "selling_price_list"
                    ) or frappe.db.get_value("Price List", _("Standard Selling"))
                
                if default_price_list and frappe.db.exists("Price List", default_price_list):
                    # Check if price already exists
                    existing_price = frappe.db.exists(
                        "Item Price",
                        {"item_code": item_code, "price_list": default_price_list}
                    )
                    
                    if not existing_price:
                        item_price = frappe.new_doc("Item Price")
                        item_price.price_list = default_price_list
                        item_price.item_code = item_code
                        item_price.uom = stock_uom
                        item_price.brand = brand
                        item_price.currency = erpnext.get_default_currency()
                        item_price.price_list_rate = flt(temp_standard_rate)
                        item_price.insert(ignore_permissions=True)
            except Exception:
                # If price creation fails, log but don't fail the item creation
                frappe.log_error(
                    f"Failed to create Item Price for {item_code}: {frappe.get_traceback()}",
                    "Item Price Creation Error"
                )
        
        frappe.db.commit()
        
        # Set HTTP status code
        frappe.local.response["http_status_code"] = 201
        
        return {
            "product": {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "item_group": item.item_group,
                "stock_uom": item.stock_uom,
                "standard_rate": item.standard_rate,
                "is_stock_item": item.is_stock_item,
                "is_sales_item": item.is_sales_item,
                "is_purchase_item": item.is_purchase_item,
                "disabled": item.disabled
            },
            "message": _("Product created successfully")
        }
    
    except frappe.AuthenticationError:
        # Re-raise authentication errors as-is
        raise
    except frappe.ValidationError:
        # Re-raise validation errors as-is (they already have user-friendly messages)
        raise
    except frappe.DuplicateEntryError as e:
        # Handle duplicate entry errors
        frappe.throw(
            _("A product with this information already exists. Please check the product code '{0}' and try again with a unique code.").format(item_code),
            frappe.ValidationError
        )
    except frappe.MandatoryError as e:
        # Handle missing mandatory fields
        error_msg = str(e)
        if "item_code" in error_msg.lower():
            frappe.throw(_("Product code is required. Please provide a unique code for this product."), frappe.ValidationError)
        elif "item_name" in error_msg.lower():
            frappe.throw(_("Product name is required. Please provide a name for this product."), frappe.ValidationError)
        else:
            frappe.throw(_("Some required information is missing: {0}. Please fill in all required fields and try again.").format(error_msg), frappe.ValidationError)
    except frappe.PermissionError as e:
        # Handle permission errors
        frappe.throw(
            _("You don't have permission to create products. Please contact your administrator to grant you the necessary permissions."),
            frappe.PermissionError
        )
    except Exception as e:
        # Log the full error for debugging
        frappe.log_error(
            f"Error creating product '{item_code}': {frappe.get_traceback()}",
            "Product Creation Error"
        )
        # Return user-friendly error message
        frappe.throw(
            _("An error occurred while creating the product. Please check that all information is correct and try again. If the problem persists, contact support."),
            frappe.ValidationError
        )


@frappe.whitelist()
def get_products(
    company: str = None,
    item_group: str = None,
    brand: str = None,
    is_stock_item: bool = None,
    is_sales_item: bool = None,
    disabled: bool = False,
    search_term: str = None,
    page: int = 1,
    page_size: int = 20,
    price_list: str = None
) -> Dict:
    """Get list of products with filtering and pagination
    
    Args:
        company: Filter by company
        item_group: Filter by item group
        brand: Filter by brand
        is_stock_item: Filter by stock item status
        is_sales_item: Filter by sales item status
        disabled: Include disabled items (default: false)
        search_term: Search in item_code, item_name, description
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
        price_list: Price list to get prices from (optional, will use default if not provided)
        
    Returns:
        List of products with pagination info
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Get default price list if not provided
    if not price_list:
        if company:
            # Get default selling price list from company
            price_list = frappe.db.get_value(
                "Price List",
                {"enabled": 1, "selling": 1},
                "name",
                order_by="creation desc"
            )
        if not price_list:
            # Get from Selling Settings
            price_list = frappe.get_single_value("Selling Settings", "selling_price_list")
        if not price_list:
            # Try to get "Standard Selling" price list
            price_list = frappe.db.get_value("Price List", _("Standard Selling"), "name")
    
    # Get company for filtering (required for product isolation)
    if not company:
        company = frappe.defaults.get_user_default("Company")
        if not company:
            return {
                "success": False,
                "message": "Company is required for product listing. Please set a default company or provide company parameter.",
                "data": {
                    "products": [],
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": 0,
                        "total_pages": 0
                    }
                }
            }
    
    # Get user's POS industry for filtering
    user_industry = frappe.db.get_value("User", frappe.session.user, "custom_pos_industry")
    
    # Build filters
    filters = {}
    # Company isolation - only show products for the user's company
    filters["custom_company"] = company
    if not disabled:
        filters["disabled"] = 0
    if item_group:
        filters["item_group"] = item_group
    if brand:
        filters["brand"] = brand
    if is_stock_item is not None:
        filters["is_stock_item"] = 1 if is_stock_item else 0
    if is_sales_item is not None:
        filters["is_sales_item"] = 1 if is_sales_item else 0
    
    # Build industry filter - show products that are either:
    # 1. Not linked to any industry (custom_pos_industry is NULL) - available to all
    # 2. Linked to the user's industry
    industry_filters = None
    if user_industry:
        industry_filters = [
            ["custom_pos_industry", "is", "not set"],
            ["custom_pos_industry", "=", user_industry]
        ]
    
    # Build search conditions
    search_conditions = None
    if search_term:
        search_conditions = [
            ["item_code", "like", f"%{search_term}%"],
            ["item_name", "like", f"%{search_term}%"],
            ["description", "like", f"%{search_term}%"]
        ]
    
    # Get total count - need to handle industry filter separately since it's an OR condition
    if industry_filters:
        # Use SQL for complex filtering with OR condition
        total = frappe.db.sql("""
            SELECT COUNT(*) 
            FROM `tabItem`
            WHERE custom_company = %(company)s
            AND disabled = %(disabled)s
            AND (custom_pos_industry IS NULL OR custom_pos_industry = %(industry)s)
        """, {
            "company": company,
            "disabled": 0 if not disabled else 1,
            "industry": user_industry
        })[0][0]
    else:
        total = frappe.db.count("Item", filters=filters)
    
    # Get paginated results
    start = (page - 1) * page_size
    
    # Handle industry filtering with SQL for complex OR condition
    if industry_filters:
        # Build WHERE clause for industry filter
        industry_where = " AND (custom_pos_industry IS NULL OR custom_pos_industry = %(industry)s)"
        
        # Build WHERE clause for other filters
        where_clauses = ["custom_company = %(company)s"]
        params = {"company": company, "industry": user_industry}
        
        if not disabled:
            where_clauses.append("disabled = 0")
        else:
            where_clauses.append("disabled = 1")
        
        if item_group:
            where_clauses.append("item_group = %(item_group)s")
            params["item_group"] = item_group
        
        if brand:
            where_clauses.append("brand = %(brand)s")
            params["brand"] = brand
        
        if is_stock_item is not None:
            where_clauses.append(f"is_stock_item = {1 if is_stock_item else 0}")
        
        if is_sales_item is not None:
            where_clauses.append(f"is_sales_item = {1 if is_sales_item else 0}")
        
        # Build search conditions
        search_where = ""
        if search_term:
            search_where = " AND (item_code LIKE %(search)s OR item_name LIKE %(search)s OR description LIKE %(search)s)"
            params["search"] = f"%{search_term}%"
        
        where_sql = " AND ".join(where_clauses) + industry_where + search_where
        
        products = frappe.db.sql(f"""
            SELECT name, item_code, item_name, item_group, stock_uom,
                   standard_rate, is_stock_item, is_sales_item, is_purchase_item,
                   disabled, brand, image
            FROM `tabItem`
            WHERE {where_sql}
            ORDER BY creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {
            **params,
            "limit": page_size,
            "offset": start
        }, as_dict=True)
    else:
        products = frappe.get_all(
            "Item",
            fields=[
                "name", "item_code", "item_name", "item_group", "stock_uom",
                "standard_rate", "is_stock_item", "is_sales_item", "is_purchase_item",
                "disabled", "brand", "image"
            ],
            filters=filters,
            or_filters=search_conditions,
            limit=page_size,
            start=start,
            order_by="creation desc"
        )
    
    # Get prices from Item Price for each product if price_list is available
    if price_list and frappe.db.exists("Price List", price_list):
        item_codes = [p["item_code"] for p in products]
        if item_codes:
            # Fetch all prices for these items in one query
            # Item Price uniqueness is based on item_code, price_list, uom, and optional fields
            # We'll fetch all matching prices and then match by UOM
            item_prices = frappe.db.get_all(
                "Item Price",
                filters={
                    "item_code": ["in", item_codes],
                    "price_list": price_list
                },
                fields=["item_code", "price_list_rate", "currency", "uom"]
            )
            
            # Create a dictionary for quick lookup: item_code -> list of prices
            price_map = {}
            for ip in item_prices:
                item_code = ip["item_code"]
                if item_code not in price_map:
                    price_map[item_code] = []
                price_map[item_code].append(ip)
            
            # Get price list currency for fallback
            price_list_currency = frappe.db.get_value("Price List", price_list, "currency")
            
            # Map prices to products
            for product in products:
                item_code = product["item_code"]
                stock_uom = product.get("stock_uom")
                
                # Try to find price with matching UOM first
                item_price = None
                if item_code in price_map:
                    prices = price_map[item_code]
                    # Prefer exact UOM match
                    for ip in prices:
                        if ip.get("uom") == stock_uom:
                            item_price = ip
                            break
                    # If no exact match, use first available price
                    if not item_price and prices:
                        item_price = prices[0]
                
                if item_price:
                    product["price"] = item_price["price_list_rate"]
                    product["price_currency"] = item_price.get("currency") or price_list_currency
                    product["price_list"] = price_list
                    product["price_source"] = "price_list"
                else:
                    # Fallback to standard_rate
                    product["price"] = product.get("standard_rate") or 0
                    product["price_source"] = "standard_rate"
                    product["price_currency"] = price_list_currency
    else:
        # No price list, use standard_rate as fallback
        for product in products:
            product["price"] = product.get("standard_rate") or 0
            product["price_source"] = "standard_rate"
    
    # Get stock quantities if company provided
    if company:
        from erpnext.stock.utils import get_stock_balance
        for product in products:
            try:
                product["stock_qty"] = get_stock_balance(
                    product["item_code"],
                    None,
                    nowdate()
                )
            except Exception:
                product["stock_qty"] = 0
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "products": products,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        },
        "price_list": price_list if price_list else None
    }


@frappe.whitelist()
def get_product_details(item_code: str, company: str = None) -> Dict:
    """Get detailed information about a specific product
    
    Args:
        item_code: Product item code
        company: Company for stock and pricing info
        
    Returns:
        Detailed product information
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get item document
    item = frappe.get_doc("Item", item_code)
    
    # Build response
    product_data = {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "stock_uom": item.stock_uom,
        "standard_rate": item.standard_rate,
        "valuation_rate": item.valuation_rate,
        "description": item.description,
        "is_stock_item": item.is_stock_item,
        "is_sales_item": item.is_sales_item,
        "is_purchase_item": item.is_purchase_item,
        "disabled": item.disabled,
        "brand": item.brand,
        "image": item.image,
        "weight_per_unit": item.weight_per_unit,
        "weight_uom": item.weight_uom,
        "variant_of": item.variant_of,
        "has_variants": item.has_variants,
        "warranty_period": item.warranty_period
    }
    
    # Get stock quantity if company provided
    if company and item.is_stock_item:
        from erpnext.stock.utils import get_stock_balance
        try:
            product_data["stock_qty"] = get_stock_balance(
                item_code,
                None,
                nowdate()
            )
        except Exception:
            product_data["stock_qty"] = 0
    
    # Get prices if company provided
    if company:
        price_lists = frappe.get_all(
            "Item Price",
            filters={"item_code": item_code},
            fields=["price_list", "price_list_rate", "currency"],
            limit=5
        )
        product_data["prices"] = price_lists
    
    # Get barcodes
    barcodes = [b.barcode for b in item.barcodes]
    if barcodes:
        product_data["barcodes"] = barcodes
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "product": product_data
    }


@frappe.whitelist()
def update_product(
    item_code: str,
    item_name: str = None,
    item_group: str = None,
    stock_uom: str = None,
    standard_rate: float = None,
    description: str = None,
    is_stock_item: bool = None,
    is_sales_item: bool = None,
    is_purchase_item: bool = None,
    brand: str = None,
    image: str = None,
    weight_per_unit: float = None,
    weight_uom: str = None,
    disabled: bool = None
) -> Dict:
    """Update an existing product/item
    
    Args:
        item_code: Item code to update
        item_name: New item name
        item_group: New item group
        stock_uom: New stock UOM
        standard_rate: New standard rate
        description: New description
        is_stock_item: New stock item status
        is_sales_item: New sales item status
        is_purchase_item: New purchase item status
        brand: New brand
        image: New image
        weight_per_unit: New weight per unit
        weight_uom: New weight UOM
        disabled: Disabled status
        
    Returns:
        Updated product details
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get item document
    item = frappe.get_doc("Item", item_code)
    
    # Update fields
    if item_name is not None:
        item.item_name = item_name
    if item_group is not None:
        if not frappe.db.exists("Item Group", item_group):
            frappe.throw(_("Item Group {0} does not exist").format(item_group))
        item.item_group = item_group
    if stock_uom is not None:
        if not frappe.db.exists("UOM", stock_uom):
            frappe.throw(_("Unit of Measure {0} does not exist").format(stock_uom))
        item.stock_uom = stock_uom
    if standard_rate is not None:
        item.standard_rate = flt(standard_rate)
    if description is not None:
        item.description = description
    if is_stock_item is not None:
        item.is_stock_item = 1 if is_stock_item else 0
    if is_sales_item is not None:
        item.is_sales_item = 1 if is_sales_item else 0
    if is_purchase_item is not None:
        item.is_purchase_item = 1 if is_purchase_item else 0
    if brand is not None:
        item.brand = brand
    if image is not None:
        item.image = image
    if weight_per_unit is not None:
        item.weight_per_unit = flt(weight_per_unit)
    if weight_uom is not None:
        item.weight_uom = weight_uom
    if disabled is not None:
        item.disabled = 1 if disabled else 0
    
    item.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "product": {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "stock_uom": item.stock_uom,
            "standard_rate": item.standard_rate,
            "is_stock_item": item.is_stock_item,
            "is_sales_item": item.is_sales_item,
            "is_purchase_item": item.is_purchase_item,
            "disabled": item.disabled
        },
        "message": _("Product updated successfully")
    }


@frappe.whitelist()
def delete_product(item_code: str) -> Dict:
    """Delete/disable a product/item
    
    Args:
        item_code: Item code to delete/disable
        
    Returns:
        Success message
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Disable item instead of deleting (soft delete)
    frappe.db.set_value("Item", item_code, "disabled", 1)
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "message": _("Product disabled successfully")
    }


@frappe.whitelist()
def enable_product(item_code: str) -> Dict:
    """Enable a disabled product/item
    
    Args:
        item_code: Item code to enable
        
    Returns:
        Success message
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Enable item
    frappe.db.set_value("Item", item_code, "disabled", 0)
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "message": _("Product enabled successfully")
    }


@frappe.whitelist()
def add_barcode(item_code: str, barcode: str) -> Dict:
    """Add a barcode to an item
    
    Args:
        item_code: Item code
        barcode: Barcode to add
        
    Returns:
        Success message
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get item document
    item = frappe.get_doc("Item", item_code)
    
    # Check if barcode already exists
    existing_barcodes = [b.barcode for b in item.barcodes]
    if barcode in existing_barcodes:
        frappe.throw(_("Barcode {0} already exists for this item").format(barcode))
    
    # Add barcode
    item.append("barcodes", {"barcode": barcode})
    item.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "message": _("Barcode added successfully")
    }


@frappe.whitelist()
def remove_barcode(item_code: str, barcode: str) -> Dict:
    """Remove a barcode from an item
    
    Args:
        item_code: Item code
        barcode: Barcode to remove
        
    Returns:
        Success message
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get item document
    item = frappe.get_doc("Item", item_code)
    
    # Remove barcode
    item.barcodes = [b for b in item.barcodes if b.barcode != barcode]
    item.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "message": _("Barcode removed successfully")
    }


@frappe.whitelist()
def get_product_price(item_code: str, price_list: str = None, company: str = None) -> Dict:
    """Get product price from price list
    
    Args:
        item_code: Item code
        price_list: Price list name (optional)
        company: Company for default price list
        
    Returns:
        Product price information
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get price list if not provided
    if not price_list:
        if company:
            # Get default selling price list
            price_list = frappe.db.get_value(
                "Price List",
                {"enabled": 1, "selling": 1},
                "name",
                order_by="creation desc"
            )
        if not price_list:
            frappe.throw(_("Price list is required"))
    
    # Get price
    price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list},
        ["price_list_rate", "currency"],
        as_dict=True
    )
    
    if not price:
        # Get standard rate as fallback
        standard_rate = frappe.db.get_value("Item", item_code, "standard_rate")
        currency = frappe.db.get_value("Price List", price_list, "currency")
        return {
            "item_code": item_code,
            "price_list": price_list,
            "price": standard_rate or 0,
            "currency": currency,
            "source": "standard_rate"
        }
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "item_code": item_code,
        "price_list": price_list,
        "price": price.price_list_rate,
        "currency": price.currency,
        "source": "price_list"
    }


@frappe.whitelist()
def set_product_price(
    item_code: str,
    price: float,
    price_list: str,
    currency: str = None,
    company: str = None
) -> Dict:
    """Set product price in a price list
    
    Args:
        item_code: Item code
        price: Price to set
        price_list: Price list name
        currency: Currency (optional, defaults to company currency)
        company: Company for currency default
        
    Returns:
        Success message
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Validate price list exists
    if not frappe.db.exists("Price List", price_list):
        frappe.throw(_("Price List {0} does not exist").format(price_list))
    
    # Get currency if not provided
    if not currency:
        if company:
            currency = frappe.db.get_value("Company", company, "default_currency")
        if not currency:
            currency = frappe.db.get_value("Price List", price_list, "currency")
    
    # Check if price already exists
    existing_price = frappe.db.exists(
        "Item Price",
        {"item_code": item_code, "price_list": price_list}
    )
    
    if existing_price:
        # Update existing price
        frappe.db.set_value("Item Price", existing_price, {
            "price_list_rate": flt(price),
            "currency": currency
        })
    else:
        # Create new price
        item_price = frappe.new_doc("Item Price")
        item_price.item_code = item_code
        item_price.price_list = price_list
        item_price.price_list_rate = flt(price)
        item_price.currency = currency
        item_price.selling = 1
        item_price.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "message": _("Product price set successfully")
    }


@frappe.whitelist()
def get_stock_quantity(item_code: str, company: str = None, warehouse: str = None) -> Dict:
    """Get stock quantity for a product
    
    Args:
        item_code: Item code
        company: Company (optional)
        warehouse: Warehouse (optional)
        
    Returns:
        Stock quantity information
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Validate item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    # Get stock balance
    from erpnext.stock.utils import get_stock_balance
    try:
        qty = get_stock_balance(item_code, warehouse, nowdate())
    except Exception:
        qty = 0
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "quantity": qty
    }


@frappe.whitelist()
def bulk_create_products(products: List[Dict], company: str = None) -> Dict:
    """Create multiple products in bulk
    
    Args:
        products: List of product dictionaries
        company: Company for item defaults
        
    Returns:
        Summary of created products
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if isinstance(products, str):
        products = json.loads(products)
    
    if not isinstance(products, list):
        frappe.throw(_("Products must be a list"))
    
    created = []
    failed = []
    
    for product_data in products:
        try:
            # Extract required fields
            item_code = product_data.get("item_code")
            item_name = product_data.get("item_name")
            
            if not item_code or not item_name:
                failed.append({
                    "item_code": item_code,
                    "error": "item_code and item_name are required"
                })
                continue
            
            # Create product using existing function
            result = create_product(
                item_code=item_code,
                item_name=item_name,
                item_group=product_data.get("item_group", "All Item Groups"),
                stock_uom=product_data.get("stock_uom", "Nos"),
                standard_rate=product_data.get("standard_rate", 0.0),
                description=product_data.get("description"),
                is_stock_item=product_data.get("is_stock_item", True),
                is_sales_item=product_data.get("is_sales_item", True),
                is_purchase_item=product_data.get("is_purchase_item", False),
                brand=product_data.get("brand"),
                barcode=product_data.get("barcode"),
                image=product_data.get("image"),
                company=company or product_data.get("company"),
                prevent_etims_registration=product_data.get("prevent_etims_registration", True)
            )
            created.append(result["product"])
        except Exception as e:
            failed.append({
                "item_code": product_data.get("item_code"),
                "error": str(e)
            })
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 201
    
    return {
        "created": created,
        "failed": failed,
        "total": len(products),
        "success_count": len(created),
        "failure_count": len(failed)
    }


@frappe.whitelist()
def get_item_groups() -> Dict:
    """Get all item groups/categories
    
    Returns:
        List of item groups
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    item_groups = frappe.get_all(
        "Item Group",
        fields=["name", "item_group_name", "parent_item_group", "is_group"],
        order_by="name"
    )
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "item_groups": item_groups,
        "count": len(item_groups)
    }


@frappe.whitelist()
def get_brands() -> Dict:
    """Get all brands
    
    Returns:
        List of brands
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    brands = frappe.get_all(
        "Brand",
        fields=["name", "brand"],
        order_by="name"
    )
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "brands": brands,
        "count": len(brands)
    }


@frappe.whitelist()
def get_uoms() -> Dict:
    """Get all units of measure
    
    Returns:
        List of UOMs
    """
    # Validate user permissions
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    uoms = frappe.get_all(
        "UOM",
        fields=["name", "uom_name"],
        order_by="name"
    )
    
    # Set HTTP status code
    frappe.local.response["http_status_code"] = 200
    
    return {
        "uoms": uoms,
        "count": len(uoms)
    }


# ==================== NEW ENDPOINTS ====================

@frappe.whitelist()
def bulk_update_prices(price_updates: List[Dict], price_list: str, currency: str = None, company: str = None) -> Dict:
    """Bulk update prices for multiple products
    
    Args:
        price_updates: List of dicts with item_code and price
        price_list: Price list name
        currency: Currency (optional)
        company: Company for currency default
        
    Returns:
        Summary of updated prices
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if isinstance(price_updates, str):
        price_updates = json.loads(price_updates)
    
    if not frappe.db.exists("Price List", price_list):
        frappe.throw(_("Price List {0} does not exist").format(price_list))
    
    if not currency:
        if company:
            currency = frappe.db.get_value("Company", company, "default_currency")
        if not currency:
            currency = frappe.db.get_value("Price List", price_list, "currency")
    
    updated = []
    failed = []
    
    for update in price_updates:
        try:
            item_code = update.get("item_code")
            price = update.get("price")
            
            if not item_code or price is None:
                failed.append({"item_code": item_code, "error": "item_code and price are required"})
                continue
            
            if not frappe.db.exists("Item", item_code):
                failed.append({"item_code": item_code, "error": "Item does not exist"})
                continue
            
            # Get the item to fetch stock_uom for proper Item Price matching
            stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
            if not stock_uom:
                failed.append({"item_code": item_code, "error": "Item does not have stock_uom"})
                continue
            
            # Check if price exists - use get_value to get the actual document name
            # Item Price uniqueness is based on item_code, price_list, uom, and other optional fields
            existing_price_name = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": item_code,
                    "price_list": price_list,
                    "uom": stock_uom
                },
                "name"
            )
            
            if existing_price_name:
                # Update existing price using get_doc and save to ensure validations run
                item_price = frappe.get_doc("Item Price", existing_price_name)
                item_price.price_list_rate = flt(price)
                # Currency is automatically set from Price List during validation, but update if explicitly provided
                if currency and currency != item_price.currency:
                    item_price.currency = currency
                item_price.save(ignore_permissions=True)
            else:
                # Create new price
                item_price = frappe.new_doc("Item Price")
                item_price.item_code = item_code
                item_price.price_list = price_list
                item_price.price_list_rate = flt(price)
                item_price.uom = stock_uom
                item_price.selling = 1
                # Currency will be automatically set from Price List during validation
                # but set it explicitly if provided to ensure consistency
                if currency:
                    item_price.currency = currency
                item_price.insert(ignore_permissions=True)
            
            updated.append({"item_code": item_code, "price": price})
        except Exception as e:
            failed.append({"item_code": update.get("item_code"), "error": str(e)})
    
    frappe.db.commit()
    frappe.local.response["http_status_code"] = 200
    
    return {
        "updated": updated,
        "failed": failed,
        "total": len(price_updates),
        "success_count": len(updated),
        "failure_count": len(failed)
    }


@frappe.whitelist()
def create_product_variant(
    template_item_code: str,
    variant_attributes: List[Dict],
    item_code: str = None,
    item_name: str = None,
    standard_rate: float = None
) -> Dict:
    """Create a product variant from a template
    
    Args:
        template_item_code: Template item code (must have has_variants=1)
        variant_attributes: List of dicts with attribute and attribute_value
        item_code: Optional custom item code
        item_name: Optional custom item name
        standard_rate: Optional custom price
        
    Returns:
        Created variant details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if isinstance(variant_attributes, str):
        variant_attributes = json.loads(variant_attributes)
    
    if not frappe.db.exists("Item", template_item_code):
        frappe.throw(_("Template item {0} does not exist").format(template_item_code))
    
    template = frappe.get_doc("Item", template_item_code)
    if not template.has_variants:
        frappe.throw(_("Item {0} does not have variants enabled").format(template_item_code))
    
    # Build attributes dict for variant creation
    args = {}
    for attr in variant_attributes:
        args[attr.get("attribute")] = attr.get("attribute_value")
    
    # Import variant creation function
    from erpnext.controllers.item_variant import create_variant
    
    try:
        variant = create_variant(template_item_code, args)
        
        if item_code:
            variant.item_code = item_code
        if item_name:
            variant.item_name = item_name
        if standard_rate is not None:
            variant.standard_rate = flt(standard_rate)
        
        variant.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.local.response["http_status_code"] = 201
        return {
            "variant": {
                "item_code": variant.item_code,
                "item_name": variant.item_name,
                "variant_of": variant.variant_of,
                "standard_rate": variant.standard_rate
            },
            "message": _("Product variant created successfully")
        }
    except Exception as e:
        frappe.throw(_("Error creating variant: {0}").format(str(e)))


@frappe.whitelist()
def get_product_variants(template_item_code: str) -> Dict:
    """Get all variants of a template product
    
    Args:
        template_item_code: Template item code
        
    Returns:
        List of variants
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Item", template_item_code):
        frappe.throw(_("Template item {0} does not exist").format(template_item_code))
    
    variants = frappe.get_all(
        "Item",
        filters={"variant_of": template_item_code, "disabled": 0},
        fields=["name", "item_code", "item_name", "standard_rate", "disabled"],
        order_by="item_code"
    )
    
    # Get attributes for each variant
    for variant in variants:
        attributes = frappe.get_all(
            "Item Variant Attribute",
            filters={"parent": variant.item_code},
            fields=["attribute", "attribute_value"],
            order_by="idx"
        )
        variant["attributes"] = attributes
    
    frappe.local.response["http_status_code"] = 200
    return {
        "template_item_code": template_item_code,
        "variants": variants,
        "count": len(variants)
    }


@frappe.whitelist()
def bulk_import_products(products_data: str, company: str = None) -> Dict:
    """Bulk import products from JSON string
    
    Args:
        products_data: JSON string or list of product dictionaries
        company: Company for item defaults
        
    Returns:
        Import summary
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if isinstance(products_data, str):
        try:
            products = json.loads(products_data)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON format"))
    else:
        products = products_data
    
    if not isinstance(products, list):
        frappe.throw(_("Products data must be a list"))
    
    return bulk_create_products(products, company)


@frappe.whitelist()
def bulk_import_opening_stock(
    stock_data: List[Dict],
    company: str,
    posting_date: str = None,
    warehouse: str = None
) -> Dict:
    """Bulk import opening stock for multiple items
    
    Args:
        stock_data: List of dicts with item_code, qty, and valuation_rate
        company: Company name
        posting_date: Posting date (default: today)
        warehouse: Default warehouse (optional)
        
    Returns:
        Stock reconciliation document details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if isinstance(stock_data, str):
        stock_data = json.loads(stock_data)
    
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    if not posting_date:
        posting_date = nowdate()
    
    # Create Stock Reconciliation
    stock_reco = frappe.new_doc("Stock Reconciliation")
    stock_reco.company = company
    stock_reco.purpose = "Opening Stock"
    stock_reco.posting_date = posting_date
    stock_reco.posting_time = "00:00:00"
    
    # Get default warehouse if not provided
    if not warehouse:
        warehouse = frappe.db.get_value(
            "Warehouse",
            {"company": company, "is_group": 0},
            "name",
            order_by="creation desc"
        )
    
    added_items = []
    failed_items = []
    
    for stock_item in stock_data:
        try:
            item_code = stock_item.get("item_code")
            qty = stock_item.get("qty", 0)
            valuation_rate = stock_item.get("valuation_rate", 0)
            item_warehouse = stock_item.get("warehouse", warehouse)
            
            if not item_code:
                failed_items.append({"item_code": item_code, "error": "item_code is required"})
                continue
            
            if not frappe.db.exists("Item", item_code):
                failed_items.append({"item_code": item_code, "error": "Item does not exist"})
                continue
            
            stock_reco.append("items", {
                "item_code": item_code,
                "warehouse": item_warehouse,
                "qty": flt(qty),
                "valuation_rate": flt(valuation_rate)
            })
            added_items.append(item_code)
        except Exception as e:
            failed_items.append({"item_code": stock_item.get("item_code"), "error": str(e)})
    
    if not added_items:
        frappe.throw(_("No valid items to import"))
    
    stock_reco.insert(ignore_permissions=True)
    stock_reco.submit()
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 201
    return {
        "stock_reconciliation": stock_reco.name,
        "company": company,
        "posting_date": posting_date,
        "added_items": added_items,
        "failed_items": failed_items,
        "total_items": len(stock_data),
        "success_count": len(added_items),
        "failure_count": len(failed_items)
    }


@frappe.whitelist()
def create_price_list(
    price_list_name: str,
    currency: str,
    selling: bool = True,
    buying: bool = False,
    enabled: bool = True
) -> Dict:
    """Create a new price list
    
    Args:
        price_list_name: Name of the price list
        currency: Currency code
        selling: Is selling price list (default: True)
        buying: Is buying price list (default: False)
        enabled: Is enabled (default: True)
        
    Returns:
        Created price list details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if frappe.db.exists("Price List", price_list_name):
        frappe.throw(_("Price List {0} already exists").format(price_list_name))
    
    if not frappe.db.exists("Currency", currency):
        frappe.throw(_("Currency {0} does not exist").format(currency))
    
    price_list = frappe.new_doc("Price List")
    price_list.price_list_name = price_list_name
    price_list.currency = currency
    price_list.selling = 1 if selling else 0
    price_list.buying = 1 if buying else 0
    price_list.enabled = 1 if enabled else 0
    price_list.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 201
    return {
        "price_list": {
            "name": price_list.name,
            "price_list_name": price_list.price_list_name,
            "currency": price_list.currency,
            "selling": price_list.selling,
            "buying": price_list.buying,
            "enabled": price_list.enabled
        },
        "message": _("Price list created successfully")
    }


@frappe.whitelist()
def get_price_lists(selling: bool = None, buying: bool = None, enabled: bool = True) -> Dict:
    """Get all price lists with optional filters
    
    Args:
        selling: Filter by selling price lists
        buying: Filter by buying price lists
        enabled: Filter by enabled status (default: True)
        
    Returns:
        List of price lists
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    filters = {}
    if enabled is not None:
        filters["enabled"] = 1 if enabled else 0
    if selling is not None:
        filters["selling"] = 1 if selling else 0
    if buying is not None:
        filters["buying"] = 1 if buying else 0
    
    price_lists = frappe.get_all(
        "Price List",
        fields=["name", "price_list_name", "currency", "selling", "buying", "enabled"],
        filters=filters,
        order_by="price_list_name"
    )
    
    frappe.local.response["http_status_code"] = 200
    return {
        "price_lists": price_lists,
        "count": len(price_lists)
    }


@frappe.whitelist()
def update_price_list(
    price_list_name: str,
    currency: str = None,
    selling: bool = None,
    buying: bool = None,
    enabled: bool = None
) -> Dict:
    """Update a price list
    
    Args:
        price_list_name: Name of the price list to update
        currency: New currency
        selling: New selling status
        buying: New buying status
        enabled: New enabled status
        
    Returns:
        Updated price list details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Price List", price_list_name):
        frappe.throw(_("Price List {0} does not exist").format(price_list_name))
    
    price_list = frappe.get_doc("Price List", price_list_name)
    
    if currency:
        if not frappe.db.exists("Currency", currency):
            frappe.throw(_("Currency {0} does not exist").format(currency))
        price_list.currency = currency
    if selling is not None:
        price_list.selling = 1 if selling else 0
    if buying is not None:
        price_list.buying = 1 if buying else 0
    if enabled is not None:
        price_list.enabled = 1 if enabled else 0
    
    price_list.save(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "price_list": {
            "name": price_list.name,
            "price_list_name": price_list.price_list_name,
            "currency": price_list.currency,
            "selling": price_list.selling,
            "buying": price_list.buying,
            "enabled": price_list.enabled
        },
        "message": _("Price list updated successfully")
    }


@frappe.whitelist()
def delete_price_list(price_list_name: str) -> Dict:
    """Delete a price list
    
    Args:
        price_list_name: Name of the price list to delete
        
    Returns:
        Success message
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Price List", price_list_name):
        frappe.throw(_("Price List {0} does not exist").format(price_list_name))
    
    frappe.delete_doc("Price List", price_list_name, ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "message": _("Price list deleted successfully")
    }


@frappe.whitelist()
def create_uom(uom_name: str, must_be_whole_number: bool = False) -> Dict:
    """Create a new unit of measure
    
    Args:
        uom_name: Name of the UOM (e.g., "Nos", "Kg", "Ltr")
        must_be_whole_number: Must be whole number (default: False)
        
    Returns:
        Created UOM details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if frappe.db.exists("UOM", uom_name):
        frappe.throw(_("UOM {0} already exists").format(uom_name))
    
    uom = frappe.new_doc("UOM")
    uom.uom_name = uom_name
    uom.must_be_whole_number = 1 if must_be_whole_number else 0
    uom.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 201
    return {
        "uom": {
            "name": uom.name,
            "uom_name": uom.uom_name,
            "must_be_whole_number": uom.must_be_whole_number
        },
        "message": _("UOM created successfully")
    }


@frappe.whitelist()
def update_uom(uom_name: str, new_uom_name: str = None, must_be_whole_number: bool = None) -> Dict:
    """Update a unit of measure
    
    Args:
        uom_name: Current UOM name
        new_uom_name: New UOM name
        must_be_whole_number: New must_be_whole_number status
        
    Returns:
        Updated UOM details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("UOM", uom_name):
        frappe.throw(_("UOM {0} does not exist").format(uom_name))
    
    uom = frappe.get_doc("UOM", uom_name)
    
    if new_uom_name:
        if frappe.db.exists("UOM", new_uom_name) and new_uom_name != uom_name:
            frappe.throw(_("UOM {0} already exists").format(new_uom_name))
        uom.uom_name = new_uom_name
    if must_be_whole_number is not None:
        uom.must_be_whole_number = 1 if must_be_whole_number else 0
    
    uom.save(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "uom": {
            "name": uom.name,
            "uom_name": uom.uom_name,
            "must_be_whole_number": uom.must_be_whole_number
        },
        "message": _("UOM updated successfully")
    }


@frappe.whitelist()
def delete_uom(uom_name: str) -> Dict:
    """Delete a unit of measure
    
    Args:
        uom_name: Name of the UOM to delete
        
    Returns:
        Success message
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("UOM", uom_name):
        frappe.throw(_("UOM {0} does not exist").format(uom_name))
    
    # Check if UOM is used in any items
    items_using_uom = frappe.db.count("Item", {"stock_uom": uom_name})
    if items_using_uom > 0:
        frappe.throw(_("Cannot delete UOM {0} as it is used by {1} item(s)").format(uom_name, items_using_uom))
    
    frappe.delete_doc("UOM", uom_name, ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "message": _("UOM deleted successfully")
    }


@frappe.whitelist()
def create_item_group(
    item_group_name: str,
    parent_item_group: str = "All Item Groups",
    is_group: bool = False
) -> Dict:
    """Create a new item group/category
    
    Args:
        item_group_name: Name of the item group
        parent_item_group: Parent item group (default: "All Item Groups")
        is_group: Is a group (default: False)
        
    Returns:
        Created item group details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if frappe.db.exists("Item Group", item_group_name):
        frappe.throw(_("Item Group {0} already exists").format(item_group_name))
    
    if not frappe.db.exists("Item Group", parent_item_group):
        frappe.throw(_("Parent Item Group {0} does not exist").format(parent_item_group))
    
    item_group = frappe.new_doc("Item Group")
    item_group.item_group_name = item_group_name
    item_group.parent_item_group = parent_item_group
    item_group.is_group = 1 if is_group else 0
    item_group.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 201
    return {
        "item_group": {
            "name": item_group.name,
            "item_group_name": item_group.item_group_name,
            "parent_item_group": item_group.parent_item_group,
            "is_group": item_group.is_group
        },
        "message": _("Item group created successfully")
    }


@frappe.whitelist()
def update_item_group(
    item_group_name: str,
    new_item_group_name: str = None,
    parent_item_group: str = None,
    is_group: bool = None
) -> Dict:
    """Update an item group/category
    
    Args:
        item_group_name: Current item group name
        new_item_group_name: New item group name
        parent_item_group: New parent item group
        is_group: New is_group status
        
    Returns:
        Updated item group details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Item Group", item_group_name):
        frappe.throw(_("Item Group {0} does not exist").format(item_group_name))
    
    item_group = frappe.get_doc("Item Group", item_group_name)
    
    if new_item_group_name:
        if frappe.db.exists("Item Group", new_item_group_name) and new_item_group_name != item_group_name:
            frappe.throw(_("Item Group {0} already exists").format(new_item_group_name))
        item_group.item_group_name = new_item_group_name
    if parent_item_group:
        if not frappe.db.exists("Item Group", parent_item_group):
            frappe.throw(_("Parent Item Group {0} does not exist").format(parent_item_group))
        item_group.parent_item_group = parent_item_group
    if is_group is not None:
        item_group.is_group = 1 if is_group else 0
    
    item_group.save(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "item_group": {
            "name": item_group.name,
            "item_group_name": item_group.item_group_name,
            "parent_item_group": item_group.parent_item_group,
            "is_group": item_group.is_group
        },
        "message": _("Item group updated successfully")
    }


@frappe.whitelist()
def delete_item_group(item_group_name: str) -> Dict:
    """Delete an item group/category
    
    Args:
        item_group_name: Name of the item group to delete
        
    Returns:
        Success message
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Item Group", item_group_name):
        frappe.throw(_("Item Group {0} does not exist").format(item_group_name))
    
    # Check if item group is used by any items
    items_using_group = frappe.db.count("Item", {"item_group": item_group_name})
    if items_using_group > 0:
        frappe.throw(_("Cannot delete Item Group {0} as it is used by {1} item(s)").format(item_group_name, items_using_group))
    
    frappe.delete_doc("Item Group", item_group_name, ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "message": _("Item group deleted successfully")
    }


@frappe.whitelist()
def create_brand(brand_name: str) -> Dict:
    """Create a new brand
    
    Args:
        brand_name: Name of the brand
        
    Returns:
        Created brand details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if frappe.db.exists("Brand", brand_name):
        frappe.throw(_("Brand {0} already exists").format(brand_name))
    
    brand = frappe.new_doc("Brand")
    brand.brand = brand_name
    brand.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 201
    return {
        "brand": {
            "name": brand.name,
            "brand": brand.brand
        },
        "message": _("Brand created successfully")
    }


@frappe.whitelist()
def update_brand(brand_name: str, new_brand_name: str) -> Dict:
    """Update a brand
    
    Args:
        brand_name: Current brand name
        new_brand_name: New brand name
        
    Returns:
        Updated brand details
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Brand", brand_name):
        frappe.throw(_("Brand {0} does not exist").format(brand_name))
    
    if frappe.db.exists("Brand", new_brand_name) and new_brand_name != brand_name:
        frappe.throw(_("Brand {0} already exists").format(new_brand_name))
    
    brand = frappe.get_doc("Brand", brand_name)
    brand.brand = new_brand_name
    brand.save(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "brand": {
            "name": brand.name,
            "brand": brand.brand
        },
        "message": _("Brand updated successfully")
    }


@frappe.whitelist()
def delete_brand(brand_name: str) -> Dict:
    """Delete a brand
    
    Args:
        brand_name: Name of the brand to delete
        
    Returns:
        Success message
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Brand", brand_name):
        frappe.throw(_("Brand {0} does not exist").format(brand_name))
    
    # Check if brand is used by any items
    items_using_brand = frappe.db.count("Item", {"brand": brand_name})
    if items_using_brand > 0:
        frappe.throw(_("Cannot delete Brand {0} as it is used by {1} item(s)").format(brand_name, items_using_brand))
    
    frappe.delete_doc("Brand", brand_name, ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "message": _("Brand deleted successfully")
    }


@frappe.whitelist()
def seed_global_products(company: str = None, products_data: list = None) -> Dict:
    """Seed global products (available to all industries) for a company
    
    Args:
        company: Company name. If not provided, seeds for all companies
        products_data: Optional list of product dictionaries. If not provided, uses default products
        
    Returns:
        Summary of seeding operation
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    # Only System Managers can seed products
    if "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only System Managers can seed products"), frappe.PermissionError)
    
    try:
        from savanna_pos.savanna_pos.setup.seed_global_products import (
            seed_global_products as _seed_global_products
        )
        
        result = _seed_global_products(company=company, products_data=products_data)
        
        frappe.local.response["http_status_code"] = 200
        return {
            "success": True,
            "message": _("Seeded {0} products, skipped {1} products").format(
                result["created"], result["skipped"]
            ),
            "created": result["created"],
            "skipped": result["skipped"],
            "created_products": result["created_products"],
            "skipped_products": result["skipped_products"]
        }
    except Exception as e:
        frappe.log_error(f"Error seeding global products: {str(e)}", "Seed Global Products")
        frappe.throw(_("Error seeding products: {0}").format(str(e)), frappe.ValidationError)


@frappe.whitelist()
def set_product_warranty(item_code: str, warranty_period: int, warranty_period_unit: str = "Days") -> Dict:
    """Set warranty period for a product
    
    Args:
        item_code: Item code
        warranty_period: Warranty period (number)
        warranty_period_unit: Unit (Days, Months, Years) - default: Days
        
    Returns:
        Success message
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    valid_units = ["Days", "Months", "Years"]
    if warranty_period_unit not in valid_units:
        frappe.throw(_("Warranty period unit must be one of: {0}").format(", ".join(valid_units)))
    
    item = frappe.get_doc("Item", item_code)
    item.warranty_period = warranty_period
    item.save(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.local.response["http_status_code"] = 200
    return {
        "item_code": item_code,
        "warranty_period": warranty_period,
        "warranty_period_unit": warranty_period_unit,
        "message": _("Warranty period set successfully")
    }


@frappe.whitelist()
def get_product_warranty(item_code: str) -> Dict:
    """Get warranty information for a product
    
    Args:
        item_code: Item code
        
    Returns:
        Warranty information
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
    
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} does not exist").format(item_code), frappe.DoesNotExistError)
    
    warranty_period = frappe.db.get_value("Item", item_code, "warranty_period")
    
    frappe.local.response["http_status_code"] = 200
    return {
        "item_code": item_code,
        "warranty_period": warranty_period or 0,
        "warranty_period_unit": "Days"  # Frappe stores in days
    }
