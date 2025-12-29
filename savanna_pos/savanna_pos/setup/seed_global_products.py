"""
Seed Global Products
Creates a set of global products (available to all industries) for specified companies
"""

import frappe
from frappe import _


def seed_global_products(company: str = None, products_data: list = None):
    """Seed global products for a company
    
    Args:
        company: Company name. If not provided, will seed for all companies
        products_data: List of product dictionaries. If not provided, uses default products
    """
    if not products_data:
        products_data = get_default_global_products()
    
    if not company:
        # Get all companies
        companies = frappe.get_all("Company", fields=["name"])
        if not companies:
            frappe.throw(_("No companies found. Please create a company first."))
    else:
        if not frappe.db.exists("Company", company):
            frappe.throw(_("Company {0} does not exist").format(company))
        companies = [{"name": company}]
    
    created_products = []
    skipped_products = []
    
    for company_data in companies:
        company_name = company_data["name"]
        frappe.msgprint(_("Seeding products for company: {0}").format(company_name))
        
        for product_data in products_data:
            try:
                # Check if product already exists for this company
                existing = frappe.db.exists("Item", {
                    "item_code": product_data["item_code"],
                    "custom_company": company_name
                })
                
                if existing:
                    skipped_products.append({
                        "company": company_name,
                        "item_code": product_data["item_code"],
                        "reason": "Already exists"
                    })
                    continue
                
                # Create product
                item = frappe.new_doc("Item")
                item.item_code = product_data["item_code"]
                item.item_name = product_data["item_name"]
                item.item_group = product_data.get("item_group", "All Item Groups")
                item.stock_uom = product_data.get("stock_uom", "Nos")
                item.standard_rate = product_data.get("standard_rate", 0.0)
                item.description = product_data.get("description", "")
                item.is_stock_item = product_data.get("is_stock_item", True)
                item.is_sales_item = product_data.get("is_sales_item", True)
                item.is_purchase_item = product_data.get("is_purchase_item", False)
                item.brand = product_data.get("brand")
                
                # Set as global product (no industry)
                item.custom_company = company_name
                item.custom_pos_industry = None  # Global product - available to all industries
                item.custom_prevent_etims_registration = 1
                
                # Set image if provided
                if product_data.get("image"):
                    item.image = product_data["image"]
                
                # Add item defaults
                default_warehouse = frappe.db.get_value(
                    "Warehouse",
                    {"company": company_name, "is_group": 0},
                    "name",
                    order_by="creation desc"
                )
                
                if default_warehouse:
                    item.append("item_defaults", {
                        "company": company_name,
                        "default_warehouse": default_warehouse
                    })
                
                # Add barcode if provided
                if product_data.get("barcode"):
                    item.append("barcodes", {
                        "barcode": product_data["barcode"]
                    })
                
                item.insert(ignore_permissions=True)
                
                # Create Item Price if standard_rate is provided
                if product_data.get("standard_rate", 0) > 0:
                    default_price_list = frappe.get_single_value(
                        "Selling Settings", "selling_price_list"
                    ) or frappe.db.get_value("Price List", _("Standard Selling"), "name")
                    
                    if default_price_list and frappe.db.exists("Price List", default_price_list):
                        # Check if price already exists
                        existing_price = frappe.db.exists(
                            "Item Price",
                            {"item_code": product_data["item_code"], "price_list": default_price_list}
                        )
                        
                        if not existing_price:
                            item_price = frappe.new_doc("Item Price")
                            item_price.price_list = default_price_list
                            item_price.item_code = product_data["item_code"]
                            item_price.uom = product_data.get("stock_uom", "Nos")
                            item_price.price_list_rate = product_data.get("standard_rate", 0.0)
                            item_price.currency = frappe.get_cached_value("Company", company_name, "default_currency")
                            item_price.insert(ignore_permissions=True)
                
                created_products.append({
                    "company": company_name,
                    "item_code": product_data["item_code"],
                    "item_name": product_data["item_name"]
                })
                
            except Exception as e:
                frappe.log_error(f"Error creating product {product_data.get('item_code')}: {str(e)}", "Seed Global Products")
                skipped_products.append({
                    "company": company_name,
                    "item_code": product_data.get("item_code", "Unknown"),
                    "reason": str(e)
                })
    
    frappe.db.commit()
    
    return {
        "created": len(created_products),
        "skipped": len(skipped_products),
        "created_products": created_products,
        "skipped_products": skipped_products
    }


def get_default_global_products():
    """Get default list of global products to seed
    
    Returns:
        List of product dictionaries
    """
    return [
        {
            "item_code": "GLOBAL-PEN-001",
            "item_name": "Ballpoint Pen",
            "item_group": "Stationery",
            "stock_uom": "Nos",
            "standard_rate": 20.0,
            "description": "Standard ballpoint pen - blue ink",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-NOTEBOOK-001",
            "item_name": "Notebook A4",
            "item_group": "Stationery",
            "stock_uom": "Nos",
            "standard_rate": 150.0,
            "description": "A4 size notebook with ruled pages",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-FOLDER-001",
            "item_name": "File Folder",
            "item_group": "Stationery",
            "stock_uom": "Nos",
            "standard_rate": 50.0,
            "description": "Standard file folder for documents",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-BAG-001",
            "item_name": "Shopping Bag",
            "item_group": "Packaging",
            "stock_uom": "Nos",
            "standard_rate": 5.0,
            "description": "Plastic shopping bag",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-RECEIPT-001",
            "item_name": "Thermal Receipt Paper",
            "item_group": "Consumables",
            "stock_uom": "Roll",
            "standard_rate": 200.0,
            "description": "Thermal receipt paper roll 80mm x 50mm",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-TAPE-001",
            "item_name": "Packaging Tape",
            "item_group": "Packaging",
            "stock_uom": "Roll",
            "standard_rate": 300.0,
            "description": "Clear packaging tape",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-BOX-001",
            "item_name": "Cardboard Box Small",
            "item_group": "Packaging",
            "stock_uom": "Nos",
            "standard_rate": 25.0,
            "description": "Small cardboard box for packaging",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-BOTTLE-001",
            "item_name": "Water Bottle 500ml",
            "item_group": "Beverages",
            "stock_uom": "Nos",
            "standard_rate": 50.0,
            "description": "Bottled water 500ml",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-CANDY-001",
            "item_name": "Candy Pack",
            "item_group": "Food Items",
            "stock_uom": "Nos",
            "standard_rate": 30.0,
            "description": "Assorted candy pack",
            "is_stock_item": True,
            "is_sales_item": True,
            "is_purchase_item": False,
            "brand": "Generic"
        },
        {
            "item_code": "GLOBAL-CHARGE-001",
            "item_name": "Service Charge",
            "item_group": "Services",
            "stock_uom": "Nos",
            "standard_rate": 0.0,
            "description": "General service charge",
            "is_stock_item": False,
            "is_sales_item": True,
            "is_purchase_item": False
        }
    ]

