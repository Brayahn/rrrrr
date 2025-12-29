"""
Inventory Management API
Handles stock operations, stock entries, stock reconciliation, stock transfers, and stock queries
"""

import frappe
from frappe import _
from frappe.query_builder import DocType
from typing import Dict, List, Optional, Union
from frappe.utils import flt, cint, cstr, nowdate, getdate, nowtime, get_datetime
from datetime import datetime
import json
from erpnext.stock.utils import get_stock_balance
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from erpnext.stock.get_item_details import get_bin_details
from savanna_pos.savanna_pos.doctype.inventory_discount_rule.inventory_discount_rule import (
    get_applicable_inventory_discount,
)


@frappe.whitelist()
def get_stock_balance_api(
    item_code: str,
    warehouse: str = None,
    posting_date: str = None,
    posting_time: str = None,
    company: str = None,
) -> Dict:
    """
    Get stock balance for an item in a warehouse.
    
    Args:
        item_code: Item code to check
        warehouse: Warehouse name (optional, uses default if not provided)
        posting_date: Date to check balance at (optional, defaults to today)
        posting_time: Time to check balance at (optional)
        company: Company name (optional, uses default if not provided)
    
    Returns:
        dict: Stock balance information
    """
    try:
        # Validate item exists
        if not frappe.db.exists("Item", item_code):
            return {
                "success": False,
                "message": f"Item '{item_code}' does not exist",
            }
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Get warehouse if not provided
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Item Default",
                {"parent": item_code, "company": company},
                "default_warehouse"
            )
            if not warehouse:
                # Try to get default warehouse from company
                warehouse = frappe.db.get_value("Company", company, "default_warehouse")
                if not warehouse:
                    return {
                        "success": False,
                        "message": "Warehouse is required. Please provide warehouse parameter or set default warehouse.",
                    }
        
        # Validate warehouse exists
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Get stock balance
        balance = get_stock_balance(
            item_code=item_code,
            warehouse=warehouse,
            posting_date=posting_date or nowdate(),
            posting_time=posting_time or nowtime(),
        )
        
        # Get bin details for additional information
        bin_details = get_bin_details(item_code, warehouse, company=company)
        
        # Get additional bin information directly from Bin document
        bin_name = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "name")
        additional_bin_data = {}
        if bin_name:
            additional_bin_data = frappe.db.get_value(
                "Bin",
                bin_name,
                ["ordered_qty", "stock_value", "valuation_rate"],
                as_dict=True
            ) or {}
        
        return {
            "success": True,
            "data": {
                "item_code": item_code,
                "warehouse": warehouse,
                "balance": flt(balance, 4),
                "actual_qty": flt(bin_details.get("actual_qty", 0), 4) if bin_details else 0,
                "reserved_qty": flt(bin_details.get("reserved_qty", 0), 4) if bin_details else 0,
                "ordered_qty": flt(additional_bin_data.get("ordered_qty", 0), 4),
                "projected_qty": flt(bin_details.get("projected_qty", 0), 4) if bin_details else 0,
                "stock_value": flt(additional_bin_data.get("stock_value", 0), 4),
                "valuation_rate": flt(additional_bin_data.get("valuation_rate", 0), 4),
                "posting_date": posting_date or nowdate(),
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting stock balance: {str(e)}", "Get Stock Balance Error")
        return {
            "success": False,
            "message": f"Error getting stock balance: {str(e)}",
        }


@frappe.whitelist()
def get_stock_balance_multiple(
    items: Union[str, List[str]],
    warehouse: str = None,
    company: str = None,
) -> Dict:
    """
    Get stock balance for multiple items.
    
    Args:
        items: JSON string or list of item codes
        warehouse: Warehouse name (optional, uses default if not provided)
        company: Company name (optional, uses default if not provided)
    
    Returns:
        dict: Stock balance information for all items
    """
    try:
        # Parse items
        if isinstance(items, str):
            items = json.loads(items)
        
        if not isinstance(items, list):
            return {
                "success": False,
                "message": "Items must be a list of item codes",
            }
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        results = []
        for item_code in items:
            result = get_stock_balance_api(
                item_code=item_code,
                warehouse=warehouse,
                company=company,
            )
            if result.get("success"):
                results.append(result["data"])
            else:
                results.append({
                    "item_code": item_code,
                    "error": result.get("message"),
                })
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
        }
    except Exception as e:
        frappe.log_error(f"Error getting stock balance for multiple items: {str(e)}", "Get Stock Balance Multiple Error")
        return {
            "success": False,
            "message": f"Error getting stock balance: {str(e)}",
        }


@frappe.whitelist()
def create_stock_entry(
    stock_entry_type: str,
    items: Union[str, List[Dict]],
    posting_date: str = None,
    posting_time: str = None,
    company: str = None,
    purpose: str = None,
    from_warehouse: str = None,
    to_warehouse: str = None,
    do_not_save: bool = False,
    do_not_submit: bool = False,
) -> Dict:
    """
    Create a stock entry for material receipt, issue, or transfer.
    
    Args:
        stock_entry_type: Type of stock entry (Material Receipt, Material Issue, Material Transfer, etc.)
        items: JSON string or list of items with qty, item_code, s_warehouse, t_warehouse, etc.
        posting_date: Posting date (optional, defaults to today)
        posting_time: Posting time (optional)
        company: Company name (optional, uses default if not provided)
        purpose: Purpose of stock entry (optional, auto-determined if not provided)
        from_warehouse: Source warehouse (optional, can be specified per item)
        to_warehouse: Target warehouse (optional, can be specified per item)
        do_not_save: If True, don't save the document (default: False)
        do_not_submit: If True, don't submit the document (default: False)
    
    Returns:
        dict: Created stock entry details
    """
    try:
        # Parse items
        if isinstance(items, str):
            items = json.loads(items)
        
        if not isinstance(items, list) or len(items) == 0:
            return {
                "success": False,
                "message": "Items must be a non-empty list",
            }
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Create stock entry
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = stock_entry_type
        stock_entry.company = company
        
        # Set document-level warehouses (used as defaults for items if not specified per item)
        if from_warehouse:
            stock_entry.from_warehouse = from_warehouse
        if to_warehouse:
            stock_entry.to_warehouse = to_warehouse
        
        if posting_date:
            stock_entry.posting_date = posting_date
            stock_entry.set_posting_time = 1
        
        if posting_time:
            stock_entry.posting_time = posting_time
        
        if purpose:
            stock_entry.purpose = purpose
        
        # Add items
        for item in items:
            item_code = item.get("item_code")
            if not item_code:
                return {
                    "success": False,
                    "message": "item_code is required for all items",
                }
            
            # Validate item exists
            if not frappe.db.exists("Item", item_code):
                return {
                    "success": False,
                    "message": f"Item '{item_code}' does not exist",
                }
            
            qty = flt(item.get("qty", 0))
            if qty <= 0:
                return {
                    "success": False,
                    "message": f"Quantity must be greater than 0 for item '{item_code}'",
                }
            
            s_warehouse = item.get("s_warehouse") or from_warehouse
            t_warehouse = item.get("t_warehouse") or to_warehouse
            
            # Validate warehouses
            if s_warehouse and not frappe.db.exists("Warehouse", s_warehouse):
                return {
                    "success": False,
                    "message": f"Source warehouse '{s_warehouse}' does not exist",
                }
            
            if t_warehouse and not frappe.db.exists("Warehouse", t_warehouse):
                return {
                    "success": False,
                    "message": f"Target warehouse '{t_warehouse}' does not exist",
                }
            
            stock_entry.append("items", {
                "item_code": item_code,
                "qty": qty,
                "s_warehouse": s_warehouse,
                "t_warehouse": t_warehouse,
                "basic_rate": item.get("basic_rate"),
                "conversion_factor": item.get("conversion_factor", 1.0),
                "serial_no": item.get("serial_no"),
                "batch_no": item.get("batch_no"),
                "expense_account": item.get("expense_account"),
                "cost_center": item.get("cost_center"),
            })
        
        # Validate and save
        stock_entry.validate()
        
        if not do_not_save:
            stock_entry.insert(ignore_permissions=True)
            
            if not do_not_submit:
                stock_entry.submit()
        
        return {
            "success": True,
            "message": "Stock entry created successfully",
            "data": {
                "name": stock_entry.name,
                "stock_entry_type": stock_entry.stock_entry_type,
                "company": stock_entry.company,
                "posting_date": str(stock_entry.posting_date),
                "docstatus": stock_entry.docstatus,
                "items_count": len(stock_entry.items),
            },
        }
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error creating stock entry: {str(e)}", "Create Stock Entry Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error creating stock entry: {str(e)}", "Create Stock Entry Error")
        return {
            "success": False,
            "message": f"Error creating stock entry: {str(e)}",
        }


@frappe.whitelist()
def create_material_receipt(
    items: Union[str, List[Dict]],
    target_warehouse: str,
    posting_date: str = None,
    company: str = None,
    do_not_submit: bool = False,
) -> Dict:
    """
    Create a material receipt stock entry (stock coming into warehouse).
    
    Args:
        items: JSON string or list of items with item_code and qty
        target_warehouse: Target warehouse where stock will be received
        posting_date: Posting date (optional, defaults to today)
        company: Company name (optional, uses default if not provided)
        do_not_submit: If True, don't submit the document (default: False)
    
    Returns:
        dict: Created stock entry details
    """
    return create_stock_entry(
        stock_entry_type="Material Receipt",
        items=items,
        posting_date=posting_date,
        company=company,
        to_warehouse=target_warehouse,
        do_not_submit=do_not_submit,
    )


@frappe.whitelist()
def create_material_issue(
    items: Union[str, List[Dict]],
    source_warehouse: str,
    posting_date: str = None,
    company: str = None,
    do_not_submit: bool = False,
) -> Dict:
    """
    Create a material issue stock entry (stock going out of warehouse).
    
    Args:
        items: JSON string or list of items with item_code and qty
        source_warehouse: Source warehouse where stock will be issued from
        posting_date: Posting date (optional, defaults to today)
        company: Company name (optional, uses default if not provided)
        do_not_submit: If True, don't submit the document (default: False)
    
    Returns:
        dict: Created stock entry details
    """
    return create_stock_entry(
        stock_entry_type="Material Issue",
        items=items,
        posting_date=posting_date,
        company=company,
        from_warehouse=source_warehouse,
        do_not_submit=do_not_submit,
    )


@frappe.whitelist()
def create_material_transfer(
    items: Union[str, List[Dict]],
    source_warehouse: str,
    target_warehouse: str,
    posting_date: str = None,
    company: str = None,
    do_not_submit: bool = False,
) -> Dict:
    """
    Create a material transfer stock entry (stock moving between warehouses).
    
    Args:
        items: JSON string or list of items with item_code and qty
        source_warehouse: Source warehouse
        target_warehouse: Target warehouse
        posting_date: Posting date (optional, defaults to today)
        company: Company name (optional, uses default if not provided)
        do_not_submit: If True, don't submit the document (default: False)
    
    Returns:
        dict: Created stock entry details
    """
    return create_stock_entry(
        stock_entry_type="Material Transfer",
        items=items,
        posting_date=posting_date,
        company=company,
        from_warehouse=source_warehouse,
        to_warehouse=target_warehouse,
        do_not_submit=do_not_submit,
    )


def _create_or_update_inventory_item_details(
    item_code: str,
    warehouse: str,
    company: str = None,
    buying_price: float = None,
    selling_price: float = None,
    unit_of_measure: str = None,
    sku: str = None,
    expiry_date: str = None,
    batch_no: str = None
) -> dict:
    """Helper function to create or update inventory item details using Frappe's standard methods"""
    if not company:
        company = frappe.db.get_value("Warehouse", warehouse, "company")
        if not company:
            frappe.throw(f"Company not found for warehouse {warehouse}")

    # Check if Inventory Item Details doctype exists
    if not frappe.db.exists("DocType", "Inventory Item Details"):
        # Doctype not installed yet, skip silently
        return {}

    # Check if record exists
    existing = frappe.db.get_value(
        "Inventory Item Details",
        {"item_code": item_code, "warehouse": warehouse, "company": company},
        "name"
    )

    if existing:
        doc = frappe.get_doc("Inventory Item Details", existing)
    else:
        doc = frappe.new_doc("Inventory Item Details")
        doc.item_code = item_code
        doc.warehouse = warehouse
        doc.company = company

    # Update fields if provided
    if buying_price is not None:
        doc.buying_price = buying_price
    if selling_price is not None:
        doc.selling_price = selling_price
    if unit_of_measure:
        doc.unit_of_measure = unit_of_measure
    if sku:
        doc.sku = sku
    if expiry_date:
        doc.expiry_date = expiry_date
    if batch_no:
        doc.batch_no = batch_no

    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def create_stock_reconciliation(
    items: Union[str, List[Dict]],
    warehouse: str,
    posting_date: str = None,
    posting_time: str = None,
    company: str = None,
    expense_account: str = None,
    cost_center: str = None,
    purpose: str = "Stock Reconciliation",
    do_not_submit: bool = False,
) -> Dict:
    """
    Create a stock reconciliation to adjust stock to physical count.
    
    Args:
        items: JSON string or list of items with item_code and qty (physical count)
        warehouse: Warehouse to reconcile
        posting_date: Posting date (optional, defaults to today)
        posting_time: Posting time (optional)
        company: Company name (optional, uses default if not provided)
        expense_account: Difference account for stock adjustments (optional, auto-fetched if not provided)
        cost_center: Cost center (optional, auto-fetched from company defaults if not provided)
        purpose: Purpose of reconciliation - "Stock Reconciliation" or "Opening Stock" (default: "Stock Reconciliation")
        do_not_submit: If True, don't submit the document (default: False)
    
    Returns:
        dict: Created stock reconciliation details
    """
    try:
        # Parse items
        if isinstance(items, str):
            items = json.loads(items)
        
        if not isinstance(items, list) or len(items) == 0:
            return {
                "success": False,
                "message": "Items must be a non-empty list",
            }
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Validate warehouse exists
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Check if this will be treated as an opening entry (no Stock Ledger Entries exist)
        has_existing_sle = frappe.db.sql("""select name from `tabStock Ledger Entry` limit 1""")
        is_opening_entry = (purpose == "Opening Stock" or not has_existing_sle)
        
        # Get expense_account (difference account) if not provided
        if not expense_account:
            if is_opening_entry:
                # For opening entry, need Asset/Liability account (Temporary account type preferred)
                # First try to find a Temporary account (typically used for opening entries)
                expense_account = frappe.db.get_value(
                    "Account",
                    {
                        "company": company,
                        "is_group": 0,
                        "account_type": "Temporary",
                        "disabled": 0
                    },
                    "name",
                    order_by="name asc"
                )
                
                # If no Temporary account, find any Asset/Liability account (excluding Bank)
                if not expense_account:
                    expense_account = frappe.db.get_value(
                        "Account",
                        {
                            "company": company,
                            "is_group": 0,
                            "report_type": ["in", ["Asset", "Liability"]],
                            "account_type": ["!=", "Bank"],
                            "disabled": 0
                        },
                        "name",
                        order_by="name asc"
                    )
            else:
                # For regular reconciliation, use standard ERPNext logic
                from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_difference_account
                expense_account = get_difference_account(purpose, company)
                
                # If no default account found, try to get stock adjustment account
                if not expense_account:
                    expense_account = frappe.db.get_value(
                        "Company", company, "stock_adjustment_account"
                    )
            
            if not expense_account:
                account_type_msg = "Asset/Liability type (preferably Temporary)" if is_opening_entry else "Profit and Loss type"
                return {
                    "success": False,
                    "message": f"Difference Account (expense_account) is required. Please set 'stock_adjustment_account' in Company '{company}' settings or provide expense_account parameter. For opening entries, the account must be an {account_type_msg} account. Use the 'list_stock_reconciliation_accounts' endpoint to find suitable accounts.",
                }
        else:
            # User provided an account, but we need to validate it's correct type for opening entries
            if is_opening_entry:
                account_details = frappe.db.get_value(
                    "Account",
                    expense_account,
                    ["report_type", "account_type", "disabled"],
                    as_dict=True
                )
                
                if not account_details:
                    return {
                        "success": False,
                        "message": f"Difference Account '{expense_account}' does not exist",
                    }
                
                if account_details.disabled:
                    return {
                        "success": False,
                        "message": f"Difference Account '{expense_account}' is disabled",
                    }
                
                # For opening entry, account must be Asset/Liability (not Profit and Loss)
                if account_details.report_type == "Profit and Loss":
                    return {
                        "success": False,
                        "message": f"Difference Account '{expense_account}' must be an Asset/Liability type account for Opening Stock. Current type: {account_details.report_type}. Please provide a valid Asset or Liability account in the expense_account parameter. Use the 'list_stock_reconciliation_accounts' endpoint to find suitable accounts.",
                    }
        
        # Validate expense_account exists (final check)
        if not frappe.db.exists("Account", expense_account):
            return {
                "success": False,
                "message": f"Difference Account '{expense_account}' does not exist",
            }
        
        # Get cost_center if not provided
        if not cost_center:
            cost_center = frappe.db.get_value("Company", company, "cost_center")
        
        # Create stock reconciliation
        stock_reconciliation = frappe.new_doc("Stock Reconciliation")
        # Ensure _action attribute exists to prevent AttributeError during validation
        # It will be set to "submit" by Frappe's submit() method when submitting
        stock_reconciliation._action = None
        
        stock_reconciliation.company = company
        stock_reconciliation.purpose = purpose
        stock_reconciliation.expense_account = expense_account
        if cost_center:
            stock_reconciliation.cost_center = cost_center
        
        if posting_date:
            stock_reconciliation.posting_date = posting_date
            stock_reconciliation.posting_time = posting_time or nowtime()
            stock_reconciliation.set_posting_time = 1
        
        # Add items
        for item in items:
            item_code = item.get("item_code")
            if not item_code:
                return {
                    "success": False,
                    "message": "item_code is required for all items",
                }
            
            # Validate item exists
            if not frappe.db.exists("Item", item_code):
                return {
                    "success": False,
                    "message": f"Item '{item_code}' does not exist",
                }
            
            qty = flt(item.get("qty", 0))
            if qty < 0:
                return {
                    "success": False,
                    "message": f"Quantity cannot be negative for item '{item_code}'",
                }
            
            # Get current stock balance
            current_balance = get_stock_balance(
                item_code=item_code,
                warehouse=warehouse,
                posting_date=posting_date or nowdate(),
            )
            
            stock_reconciliation.append("items", {
                "item_code": item_code,
                "warehouse": warehouse,
                "qty": qty,
                "valuation_rate": item.get("valuation_rate"),
            })
        
        # Save document (validate() is called automatically by insert())
        # _action is already set to None above, Frappe's submit() will set it to "submit" when submitting
        stock_reconciliation.insert(ignore_permissions=True)
        
        # Create or update inventory item details for each item
        inventory_items_created = []
        for idx, item in enumerate(items):
            item_code = item.get("item_code")
            buying_price = item.get("buying_price")
            selling_price = item.get("selling_price")
            uom = item.get("unit_of_measure") or item.get("uom")
            sku = item.get("sku")
            expiry_date = item.get("expiry_date")
            batch_no = item.get("batch_no")
            
            # Only create/update if at least one inventory detail is provided
            if any([buying_price is not None, selling_price is not None, uom, sku, expiry_date, batch_no]):
                try:
                    inventory_item = _create_or_update_inventory_item_details(
                        item_code=item_code,
                        warehouse=warehouse,
                        company=company,
                        buying_price=buying_price,
                        selling_price=selling_price,
                        unit_of_measure=uom,
                        sku=sku,
                        expiry_date=expiry_date,
                        batch_no=batch_no
                    )
                    inventory_items_created.append({
                        "item_code": item_code,
                        "name": inventory_item.get("name")
                    })
                except Exception as e:
                    # Log error but don't fail the stock reconciliation
                    frappe.log_error(
                        f"Error creating inventory item details for {item_code} in {warehouse}: {str(e)}",
                        "Inventory Item Details Creation Error"
                    )
        
        if not do_not_submit:
            # Frappe's submit() method will set _action = "submit" automatically
            stock_reconciliation.submit()
        
        return {
            "success": True,
            "message": "Stock reconciliation created successfully",
            "data": {
                "name": stock_reconciliation.name,
                "company": stock_reconciliation.company,
                "warehouse": warehouse,
                "posting_date": str(stock_reconciliation.posting_date),
                "docstatus": stock_reconciliation.docstatus,
                "items_count": len(stock_reconciliation.items),
                "inventory_items_created": inventory_items_created,
            },
        }
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error creating stock reconciliation: {str(e)}", "Create Stock Reconciliation Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error creating stock reconciliation: {str(e)}", "Create Stock Reconciliation Error")
        return {
            "success": False,
            "message": f"Error creating stock reconciliation: {str(e)}",
        }


@frappe.whitelist()
def check_stock_availability(
    item_code: str,
    qty: float,
    warehouse: str = None,
    company: str = None,
) -> Dict:
    """
    Check if sufficient stock is available for an item.
    
    Args:
        item_code: Item code to check
        qty: Required quantity
        warehouse: Warehouse to check (optional, uses default if not provided)
        company: Company name (optional, uses default if not provided)
    
    Returns:
        dict: Availability information
    """
    try:
        # Validate item exists
        if not frappe.db.exists("Item", item_code):
            return {
                "success": False,
                "message": f"Item '{item_code}' does not exist",
            }
        
        # Check if item is a stock item
        is_stock_item = frappe.db.get_value("Item", item_code, "is_stock_item")
        if not is_stock_item:
            return {
                "success": True,
                "data": {
                    "item_code": item_code,
                    "available": True,
                    "is_stock_item": False,
                    "message": "Item is not a stock item, no stock check required",
                },
            }
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Get warehouse if not provided
        if not warehouse:
            warehouse = frappe.db.get_value(
                "Item Default",
                {"parent": item_code, "company": company},
                "default_warehouse"
            )
            if not warehouse:
                warehouse = frappe.db.get_value("Company", company, "default_warehouse")
                if not warehouse:
                    return {
                        "success": False,
                        "message": "Warehouse is required. Please provide warehouse parameter or set default warehouse.",
                    }
        
        # Get stock balance
        balance_result = get_stock_balance_api(
            item_code=item_code,
            warehouse=warehouse,
            company=company,
        )
        
        if not balance_result.get("success"):
            return balance_result
        
        balance_data = balance_result["data"]
        available_qty = balance_data.get("projected_qty", balance_data.get("balance", 0))
        
        # Check if negative stock is allowed
        allow_negative_stock = frappe.db.get_value("Item", item_code, "allow_negative_stock") or False
        
        is_available = available_qty >= qty or allow_negative_stock
        
        return {
            "success": True,
            "data": {
                "item_code": item_code,
                "warehouse": warehouse,
                "required_qty": flt(qty, 4),
                "available_qty": flt(available_qty, 4),
                "actual_qty": balance_data.get("actual_qty", 0),
                "reserved_qty": balance_data.get("reserved_qty", 0),
                "available": is_available,
                "allow_negative_stock": allow_negative_stock,
                "shortage": flt(qty - available_qty, 4) if not is_available else 0,
            },
        }
    except Exception as e:
        frappe.log_error(f"Error checking stock availability: {str(e)}", "Check Stock Availability Error")
        return {
            "success": False,
            "message": f"Error checking stock availability: {str(e)}",
        }


@frappe.whitelist()
def get_stock_ledger_entries(
    item_code: str = None,
    warehouse: str = None,
    from_date: str = None,
    to_date: str = None,
    voucher_type: str = None,
    company: str = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict:
    """
    Get stock ledger entries with filters.
    
    Args:
        item_code: Filter by item code (optional)
        warehouse: Filter by warehouse (optional)
        from_date: Start date (optional)
        to_date: End date (optional)
        voucher_type: Filter by voucher type (optional, e.g., "Sales Invoice", "Stock Entry")
        company: Company name (optional, uses default if not provided)
        limit: Number of records to return (default: 100)
        offset: Offset for pagination (default: 0)
    
    Returns:
        dict: List of stock ledger entries
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        # Build filters
        filters = {}
        if item_code:
            filters["item_code"] = item_code
        if warehouse:
            filters["warehouse"] = warehouse
        if voucher_type:
            filters["voucher_type"] = voucher_type
        if company:
            filters["company"] = company
        if from_date:
            filters["posting_date"] = [">=", from_date]
        if to_date:
            if "posting_date" in filters:
                filters["posting_date"] = ["between", [from_date or "1900-01-01", to_date]]
            else:
                filters["posting_date"] = ["<=", to_date]
        
        # Get stock ledger entries
        entries = frappe.get_all(
            "Stock Ledger Entry",
            filters=filters,
            fields=[
                "name",
                "item_code",
                "warehouse",
                "posting_date",
                "posting_time",
                "voucher_type",
                "voucher_no",
                "actual_qty",
                "qty_after_transaction",
                "incoming_rate",
                "valuation_rate",
                "stock_value",
                "stock_value_difference",
                "is_cancelled",
            ],
            order_by="posting_date desc, posting_time desc, creation desc",
            limit=limit,
            start=offset,
        )
        
        return {
            "success": True,
            "data": entries,
            "count": len(entries),
        }
    except Exception as e:
        frappe.log_error(f"Error getting stock ledger entries: {str(e)}", "Get Stock Ledger Entries Error")
        return {
            "success": False,
            "message": f"Error getting stock ledger entries: {str(e)}",
        }


@frappe.whitelist()
def get_stock_summary(
    warehouse: str = None,
    company: str = None,
    item_group: str = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict:
    """
    Get stock summary for items in a warehouse.
    
    Args:
        warehouse: Warehouse name (optional, shows all warehouses if not provided)
        company: Company name (optional, uses default if not provided)
        item_group: Filter by item group (optional)
        limit: Number of records to return (default: 100)
        offset: Offset for pagination (default: 0)
    
    Returns:
        dict: Stock summary data
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        # Build filters for Bin
        filters = {}
        if warehouse:
            filters["warehouse"] = warehouse
        if company:
            # Get warehouses for company
            company_warehouses = frappe.get_all(
                "Warehouse",
                filters={"company": company},
                pluck="name"
            )
            if warehouse and warehouse not in company_warehouses:
                return {
                    "success": False,
                    "message": f"Warehouse '{warehouse}' does not belong to company '{company}'",
                }
            if not warehouse:
                filters["warehouse"] = ["in", company_warehouses]
        
        # Get bins
        bins = frappe.get_all(
            "Bin",
            filters=filters,
            fields=[
                "item_code",
                "warehouse",
                "actual_qty",
                "reserved_qty",
                "ordered_qty",
                "projected_qty",
                "stock_value",
                "valuation_rate",
            ],
            limit=limit,
            start=offset,
        )
        
        # Filter by item group if provided
        if item_group:
            item_codes = frappe.get_all(
                "Item",
                filters={"item_group": item_group},
                pluck="name"
            )
            bins = [b for b in bins if b["item_code"] in item_codes]
        
        # Get item details
        for bin_data in bins:
            item_code = bin_data["item_code"]
            item_details = frappe.db.get_value(
                "Item",
                item_code,
                ["item_name", "item_group", "stock_uom", "is_stock_item"],
                as_dict=True
            )
            if item_details:
                bin_data.update(item_details)
        
        return {
            "success": True,
            "data": bins,
            "count": len(bins),
        }
    except Exception as e:
        frappe.log_error(f"Error getting stock summary: {str(e)}", "Get Stock Summary Error")
        return {
            "success": False,
            "message": f"Error getting stock summary: {str(e)}",
        }


@frappe.whitelist()
def repost_stock(
    item_code: str = None,
    warehouse: str = None,
    company: str = None,
) -> Dict:
    """
    Repost stock for an item-warehouse combination.
    This recalculates stock balance from Stock Ledger Entries.
    
    Args:
        item_code: Item code (optional, reposts all items if not provided)
        warehouse: Warehouse name (optional, reposts all warehouses if not provided)
        company: Company name (optional, uses default if not provided)
    
    Returns:
        dict: Repost result
    """
    try:
        from erpnext.stock.stock_balance import repost_stock
        
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        if item_code and warehouse:
            # Repost specific item-warehouse
            repost_stock(
                item_code=item_code,
                warehouse=warehouse,
                allow_zero_rate=True,
            )
            return {
                "success": True,
                "message": f"Stock reposted successfully for item '{item_code}' in warehouse '{warehouse}'",
            }
        elif item_code:
            # Repost all warehouses for item
            warehouses = frappe.get_all(
                "Bin",
                filters={"item_code": item_code},
                pluck="warehouse"
            )
            for wh in warehouses:
                repost_stock(
                    item_code=item_code,
                    warehouse=wh,
                    allow_zero_rate=True,
                )
            return {
                "success": True,
                "message": f"Stock reposted successfully for item '{item_code}' in {len(warehouses)} warehouse(s)",
            }
        else:
            return {
                "success": False,
                "message": "Either item_code or both item_code and warehouse must be provided",
            }
    except Exception as e:
        frappe.log_error(f"Error reposting stock: {str(e)}", "Repost Stock Error")
        return {
            "success": False,
            "message": f"Error reposting stock: {str(e)}",
        }


@frappe.whitelist()
def get_low_stock_items(
    warehouse: str = None,
    company: str = None,
    threshold: float = 10.0,
    limit: int = 100,
) -> Dict:
    """
    Get items with low stock (below threshold).
    
    Args:
        warehouse: Warehouse name (optional, checks all warehouses if not provided)
        company: Company name (optional, uses default if not provided)
        threshold: Stock threshold (default: 10.0)
        limit: Number of records to return (default: 100)
    
    Returns:
        dict: List of items with low stock
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        # Build filters
        filters = {
            "actual_qty": ["<", threshold],
        }
        if warehouse:
            filters["warehouse"] = warehouse
        if company:
            company_warehouses = frappe.get_all(
                "Warehouse",
                filters={"company": company},
                pluck="name"
            )
            if warehouse and warehouse not in company_warehouses:
                return {
                    "success": False,
                    "message": f"Warehouse '{warehouse}' does not belong to company '{company}'",
                }
            if not warehouse:
                filters["warehouse"] = ["in", company_warehouses]
        
        # Get bins with low stock
        bins = frappe.get_all(
            "Bin",
            filters=filters,
            fields=[
                "item_code",
                "warehouse",
                "actual_qty",
                "reserved_qty",
                "projected_qty",
            ],
            order_by="actual_qty asc",
            limit=limit,
        )
        
        # Get item details
        for bin_data in bins:
            item_code = bin_data["item_code"]
            item_details = frappe.db.get_value(
                "Item",
                item_code,
                ["item_name", "item_group", "stock_uom"],
                as_dict=True
            )
            if item_details:
                bin_data.update(item_details)
        
        return {
            "success": True,
            "data": bins,
            "count": len(bins),
            "threshold": threshold,
        }
    except Exception as e:
        frappe.log_error(f"Error getting low stock items: {str(e)}", "Get Low Stock Items Error")
        return {
            "success": False,
            "message": f"Error getting low stock items: {str(e)}",
        }


@frappe.whitelist()
def list_stock_reconciliation_accounts(
    company: str = None,
    purpose: str = "Stock Reconciliation",
    include_disabled: bool = False,
) -> Dict:
    """
    List suitable accounts for stock reconciliation based on purpose.
    
    Args:
        company: Company name (optional, uses default if not provided)
        purpose: Purpose of reconciliation - "Stock Reconciliation" or "Opening Stock" (default: "Stock Reconciliation")
        include_disabled: Include disabled accounts (default: False)
    
    Returns:
        dict: List of suitable accounts with details
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Determine account type requirements based on purpose
        is_opening = (purpose == "Opening Stock")
        
        # Build filters
        filters = {
            "company": company,
            "is_group": 0,  # Only ledger accounts, not groups
        }
        
        if not include_disabled:
            filters["disabled"] = 0
        
        if is_opening:
            # For opening stock, need Asset/Liability accounts (preferably Temporary type)
            # First get Temporary accounts
            temp_accounts = frappe.get_all(
                "Account",
                filters={**filters, "account_type": "Temporary"},
                fields=[
                    "name",
                    "account_name",
                    "account_type",
                    "report_type",
                    "parent_account",
                    "disabled",
                ],
                order_by="account_name asc",
            )
            
            # Then get other Asset/Liability accounts (excluding Bank and Temporary)
            asset_liability_accounts = frappe.get_all(
                "Account",
                filters={
                    **filters,
                    "report_type": ["in", ["Asset", "Liability"]],
                    "account_type": ["not in", ["Bank", "Temporary"]],
                },
                fields=[
                    "name",
                    "account_name",
                    "account_type",
                    "report_type",
                    "parent_account",
                    "disabled",
                ],
                order_by="report_type, account_name asc",
            )
            
            # Combine and mark preferred accounts
            accounts = []
            for acc in temp_accounts:
                acc["preferred"] = True
                accounts.append(acc)
            for acc in asset_liability_accounts:
                acc["preferred"] = False
                accounts.append(acc)
        else:
            # For regular reconciliation, get Profit and Loss accounts
            # First try to get the default stock adjustment account
            default_account = frappe.db.get_value("Company", company, "stock_adjustment_account")
            
            accounts = frappe.get_all(
                "Account",
                filters={
                    **filters,
                    "report_type": "Profit and Loss",
                    "account_type": ["!=", "Cost of Goods Sold"],  # COGS not suitable for adjustments
                },
                fields=[
                    "name",
                    "account_name",
                    "account_type",
                    "report_type",
                    "parent_account",
                    "disabled",
                ],
                order_by="account_name asc",
            )
            
            # Mark default account as preferred
            for acc in accounts:
                acc["preferred"] = (acc["name"] == default_account)
        
        return {
            "success": True,
            "data": accounts,
            "count": len(accounts),
            "purpose": purpose,
            "is_opening": is_opening,
            "recommendation": "Use a Temporary account (preferred) or Asset/Liability account" if is_opening else "Use Profit and Loss account (Stock Adjustment account preferred)",
        }
    except Exception as e:
        frappe.log_error(f"Error listing stock reconciliation accounts: {str(e)}", "List Stock Reconciliation Accounts Error")
        return {
            "success": False,
            "message": f"Error listing accounts: {str(e)}",
        }


@frappe.whitelist()
def get_company_default_accounts(company: str = None) -> Dict:
    """
    Get default accounts configured for a company.
    
    Args:
        company: Company name (optional, uses default if not provided)
    
    Returns:
        dict: Default accounts for the company
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please set a default company or provide company parameter.",
                }
        
        # Validate company exists
        if not frappe.db.exists("Company", company):
            return {
                "success": False,
                "message": f"Company '{company}' does not exist",
            }
        
        # Get company defaults
        company_doc = frappe.get_doc("Company", company)
        
        default_accounts = {
            "stock_adjustment_account": company_doc.stock_adjustment_account,
            "cost_center": company_doc.cost_center,
            "default_warehouse": company_doc.default_warehouse,
        }
        
        # Get account details if they exist
        account_details = {}
        for key, account_name in default_accounts.items():
            if account_name:
                account_info = frappe.db.get_value(
                    "Account",
                    account_name,
                    ["account_name", "account_type", "report_type", "disabled"],
                    as_dict=True
                )
                if account_info:
                    account_details[key] = {
                        "name": account_name,
                        **account_info
                    }
                else:
                    account_details[key] = {
                        "name": account_name,
                        "error": "Account not found"
                    }
            else:
                account_details[key] = None
        
        return {
            "success": True,
            "data": {
                "company": company,
                "default_accounts": default_accounts,
                "account_details": account_details,
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting company default accounts: {str(e)}", "Get Company Default Accounts Error")
        return {
            "success": False,
            "message": f"Error getting default accounts: {str(e)}",
        }


@frappe.whitelist()
def get_inventory_item_details(
    item_code: str,
    warehouse: str,
    company: str = None
) -> Dict:
    """Get inventory item details for a specific item-warehouse combination
    
    Args:
        item_code: Item code
        warehouse: Warehouse name
        company: Company name (optional, will be fetched from warehouse if not provided)
        
    Returns:
        Inventory item details including buying price, selling price, UOM, SKU, expiry date, etc.
    """
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
        
        # Get company if not provided
        if not company:
            company = frappe.db.get_value("Warehouse", warehouse, "company")
            if not company:
                return {
                    "success": False,
                    "message": f"Company not found for warehouse '{warehouse}'",
                }
        
        # Validate item exists
        if not frappe.db.exists("Item", item_code):
            return {
                "success": False,
                "message": f"Item '{item_code}' does not exist",
            }
        
        # Validate warehouse exists
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Check if doctype exists
        if not frappe.db.exists("DocType", "Inventory Item Details"):
            return {
                "success": True,
                "data": None,
                "message": "Inventory Item Details doctype not installed",
            }
        
        # Get inventory item details using Frappe's standard methods
        filters = {
            "item_code": item_code,
            "warehouse": warehouse
        }
        if company:
            filters["company"] = company

        details = frappe.db.get_value(
            "Inventory Item Details",
            filters,
            [
                "name", "item_code", "warehouse", "company",
                "buying_price", "selling_price", "unit_of_measure",
                "sku", "expiry_date", "batch_no"
            ],
            as_dict=True
        )
        
        if details:
            return {
                "success": True,
                "data": details,
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No inventory details found for this item-warehouse combination",
            }
    except Exception as e:
        frappe.log_error(f"Error getting inventory item details: {str(e)}", "Get Inventory Item Details Error")
        return {
            "success": False,
            "message": f"Error getting inventory item details: {str(e)}",
        }


@frappe.whitelist()
def list_inventory_items(
    warehouse: str = None,
    company: str = None,
    item_code: str = None,
    page: int = 1,
    page_size: int = 20,
    search_term: str = None
) -> Dict:
    """List inventory items with their warehouse-level details
    
    Args:
        warehouse: Filter by warehouse
        company: Filter by company (required if warehouse not provided)
        item_code: Filter by item code
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
        search_term: Search in item_code, sku
        
    Returns:
        List of inventory items with pagination
    """
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
        
        # Get company if not provided
        if not company and warehouse:
            company = frappe.db.get_value("Warehouse", warehouse, "company")
        
        if not company:
            company = frappe.defaults.get_user_default("Company")
            if not company:
                return {
                    "success": False,
                    "message": "Company is required. Please provide company or warehouse parameter.",
                    "data": {
                        "items": [],
                        "pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total": 0,
                            "total_pages": 0
                        }
                    }
                }
        
        # Build filters
        filters = {"company": company}
        if warehouse:
            filters["warehouse"] = warehouse
        if item_code:
            filters["item_code"] = item_code
        
        # Build search conditions
        search_conditions = None
        if search_term:
            search_conditions = [
                ["item_code", "like", f"%{search_term}%"],
                ["sku", "like", f"%{search_term}%"]
            ]
        
        # Get total count
        total = frappe.db.count("Inventory Item Details", filters=filters)
        
        # Get paginated results
        start = (page - 1) * page_size
        items = frappe.get_all(
            "Inventory Item Details",
            fields=[
                "name", "item_code", "warehouse", "company",
                "buying_price", "selling_price", "unit_of_measure",
                "sku", "expiry_date", "batch_no"
            ],
            filters=filters,
            or_filters=search_conditions,
            limit=page_size,
            start=start,
            order_by="modified desc"
        )
        
        # Get item names for better display
        for item in items:
            item_name = frappe.db.get_value("Item", item["item_code"], "item_name")
            item["item_name"] = item_name
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages
                }
            }
        }
    except Exception as e:
        frappe.log_error(f"Error listing inventory items: {str(e)}", "List Inventory Items Error")
        return {
            "success": False,
            "message": f"Error listing inventory items: {str(e)}",
        }


@frappe.whitelist()
def update_inventory_item_details(
    item_code: str,
    warehouse: str,
    company: str = None,
    buying_price: float = None,
    selling_price: float = None,
    unit_of_measure: str = None,
    sku: str = None,
    expiry_date: str = None,
    batch_no: str = None
) -> Dict:
    """Update inventory item details for a specific item-warehouse combination
    
    Args:
        item_code: Item code
        warehouse: Warehouse name
        company: Company name (optional, will be fetched from warehouse if not provided)
        buying_price: Buying price (optional)
        selling_price: Selling price (optional)
        unit_of_measure: Unit of measure (optional)
        sku: SKU code (optional)
        expiry_date: Expiry date (optional, format: YYYY-MM-DD)
        batch_no: Batch number (optional)
        
    Returns:
        Updated inventory item details
    """
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)
        
        # Get company if not provided
        if not company:
            company = frappe.db.get_value("Warehouse", warehouse, "company")
            if not company:
                return {
                    "success": False,
                    "message": f"Company not found for warehouse '{warehouse}'",
                }
        
        # Validate item exists
        if not frappe.db.exists("Item", item_code):
            return {
                "success": False,
                "message": f"Item '{item_code}' does not exist",
            }
        
        # Validate warehouse exists
        if not frappe.db.exists("Warehouse", warehouse):
            return {
                "success": False,
                "message": f"Warehouse '{warehouse}' does not exist",
            }
        
        # Check if doctype exists
        if not frappe.db.exists("DocType", "Inventory Item Details"):
            return {
                "success": False,
                "message": "Inventory Item Details doctype not installed. Please run 'bench migrate' to install it.",
            }
        
        inventory_item = _create_or_update_inventory_item_details(
            item_code=item_code,
            warehouse=warehouse,
            company=company,
            buying_price=buying_price,
            selling_price=selling_price,
            unit_of_measure=unit_of_measure,
            sku=sku,
            expiry_date=expiry_date,
            batch_no=batch_no
        )
        
        return {
            "success": True,
            "message": "Inventory item details updated successfully",
            "data": inventory_item,
        }
    except Exception as e:
        frappe.log_error(f"Error updating inventory item details: {str(e)}", "Update Inventory Item Details Error")
        return {
            "success": False,
            "message": f"Error updating inventory item details: {str(e)}",
        }


def _serialize_discount_rule(rule: Dict) -> Dict:
    """Return a trimmed payload for discount rules."""
    keys = [
        "name",
        "rule_type",
        "item_code",
        "batch_no",
        "item_group",
        "warehouse",
        "company",
        "discount_type",
        "discount_value",
        "priority",
        "is_active",
        "valid_from",
        "valid_upto",
        "description",
    ]
    return {k: rule.get(k) for k in keys}


@frappe.whitelist()
def create_inventory_discount_rule(
    rule_type: str,
    company: str,
    discount_type: str,
    discount_value: float,
    item_code: str = None,
    batch_no: str = None,
    item_group: str = None,
    warehouse: str = None,
    priority: int = 10,
    is_active: int = 1,
    valid_from: str = None,
    valid_upto: str = None,
    description: str = None,
    naming_series: str = None,
) -> Dict:
    """Create an inventory discount rule (item, batch, or item group)."""
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)

        doc = frappe.new_doc("Inventory Discount Rule")
        # Set naming series - use provided value or default from doctype
        if naming_series:
            doc.naming_series = naming_series
        else:
            # Use default naming series from doctype (INV-DISC-.#####)
            # This ensures the naming_series field is set before insert
            doc.naming_series = "INV-DISC-.#####"
        doc.rule_type = rule_type
        doc.company = company
        doc.discount_type = discount_type
        doc.discount_value = flt(discount_value)
        doc.item_code = item_code
        doc.batch_no = batch_no
        doc.item_group = item_group
        doc.warehouse = warehouse
        doc.priority = priority
        doc.is_active = cint(is_active)
        doc.valid_from = valid_from
        doc.valid_upto = valid_upto
        doc.description = description
        doc.insert(ignore_permissions=True)
        return {
            "success": True,
            "message": "Inventory discount rule created",
            "data": _serialize_discount_rule(doc.as_dict()),
        }
    except Exception as e:
        frappe.log_error(f"Error creating inventory discount rule: {str(e)}", "Create Inventory Discount Rule Error")
        return {
            "success": False,
            "message": f"Error creating inventory discount rule: {str(e)}",
        }


@frappe.whitelist()
def update_inventory_discount_rule(
    name: str,
    rule_type: str = None,
    company: str = None,
    discount_type: str = None,
    discount_value: float = None,
    item_code: str = None,
    batch_no: str = None,
    item_group: str = None,
    warehouse: str = None,
    priority: int = None,
    is_active: int = None,
    valid_from: str = None,
    valid_upto: str = None,
    description: str = None,
) -> Dict:
    """Update an inventory discount rule."""
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)

        if not frappe.db.exists("Inventory Discount Rule", name):
            return {"success": False, "message": _("Inventory Discount Rule {0} not found").format(name)}

        doc = frappe.get_doc("Inventory Discount Rule", name)
        if rule_type:
            doc.rule_type = rule_type
        if company:
            doc.company = company
        if discount_type:
            doc.discount_type = discount_type
        if discount_value is not None:
            doc.discount_value = flt(discount_value)
        if item_code is not None:
            doc.item_code = item_code
        if batch_no is not None:
            doc.batch_no = batch_no
        if item_group is not None:
            doc.item_group = item_group
        if warehouse is not None:
            doc.warehouse = warehouse
        if priority is not None:
            doc.priority = priority
        if is_active is not None:
            doc.is_active = cint(is_active)
        if valid_from is not None:
            doc.valid_from = valid_from
        if valid_upto is not None:
            doc.valid_upto = valid_upto
        if description is not None:
            doc.description = description

        doc.save(ignore_permissions=True)
        return {
            "success": True,
            "message": "Inventory discount rule updated",
            "data": _serialize_discount_rule(doc.as_dict()),
        }
    except Exception as e:
        frappe.log_error(f"Error updating inventory discount rule: {str(e)}", "Update Inventory Discount Rule Error")
        return {
            "success": False,
            "message": f"Error updating inventory discount rule: {str(e)}",
        }


@frappe.whitelist()
def delete_inventory_discount_rule(name: str) -> Dict:
    """Delete an inventory discount rule."""
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Not authenticated"), frappe.AuthenticationError)

        if not frappe.db.exists("Inventory Discount Rule", name):
            return {"success": False, "message": _("Inventory Discount Rule {0} not found").format(name)}

        frappe.delete_doc("Inventory Discount Rule", name, ignore_permissions=True)
        return {"success": True, "message": "Inventory discount rule deleted"}
    except Exception as e:
        frappe.log_error(f"Error deleting inventory discount rule: {str(e)}", "Delete Inventory Discount Rule Error")
        return {
            "success": False,
            "message": f"Error deleting inventory discount rule: {str(e)}",
        }


@frappe.whitelist()
def get_inventory_discount_rule(name: str) -> Dict:
    """Fetch a single inventory discount rule."""
    try:
        if not frappe.db.exists("Inventory Discount Rule", name):
            return {"success": False, "message": _("Inventory Discount Rule {0} not found").format(name)}
        doc = frappe.get_doc("Inventory Discount Rule", name)
        return {"success": True, "data": _serialize_discount_rule(doc.as_dict())}
    except Exception as e:
        frappe.log_error(f"Error fetching inventory discount rule: {str(e)}", "Get Inventory Discount Rule Error")
        return {
            "success": False,
            "message": f"Error fetching inventory discount rule: {str(e)}",
        }


@frappe.whitelist()
def list_inventory_discount_rules(
    rule_type: str = None,
    company: str = None,
    item_code: str = None,
    batch_no: str = None,
    item_group: str = None,
    warehouse: str = None,
    is_active: int = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """List inventory discount rules with filters and pagination."""
    try:
        filters = {}
        if rule_type:
            filters["rule_type"] = rule_type
        if company:
            filters["company"] = company
        if item_code:
            filters["item_code"] = item_code
        if batch_no:
            filters["batch_no"] = batch_no
        if item_group:
            filters["item_group"] = item_group
        if warehouse:
            filters["warehouse"] = warehouse
        if is_active is not None:
            filters["is_active"] = cint(is_active)

        total = frappe.db.count("Inventory Discount Rule", filters=filters)
        rules = frappe.get_all(
            "Inventory Discount Rule",
            fields=[
                "name",
                "rule_type",
                "item_code",
                "batch_no",
                "item_group",
                "warehouse",
                "company",
                "discount_type",
                "discount_value",
                "priority",
                "is_active",
                "valid_from",
                "valid_upto",
                "description",
            ],
            filters=filters,
            limit=page_size,
            start=(page - 1) * page_size,
            order_by="priority asc, modified desc",
        )

        return {
            "success": True,
            "data": {
                "rules": [_serialize_discount_rule(r) for r in rules],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total else 0,
                },
            },
        }
    except Exception as e:
        frappe.log_error(f"Error listing inventory discount rules: {str(e)}", "List Inventory Discount Rules Error")
        return {
            "success": False,
            "message": f"Error listing inventory discount rules: {str(e)}",
        }


@frappe.whitelist()
def get_inventory_discount_for_item(
    item_code: str,
    company: str,
    warehouse: str = None,
    batch_no: str = None,
    item_group: str = None,
    posting_date: str = None,
) -> Dict:
    """Return the applicable discount rule for an item (batch > item > item group)."""
    try:
        if not item_code:
            frappe.throw(_("item_code is required"), frappe.ValidationError)
        if not company:
            frappe.throw(_("company is required"), frappe.ValidationError)

        if not item_group:
            item_group = frappe.db.get_value("Item", item_code, "item_group")

        rule = get_applicable_inventory_discount(
            item_code=item_code,
            company=company,
            warehouse=warehouse,
            batch_no=batch_no,
            item_group=item_group,
            posting_date=posting_date,
        )

        return {
            "success": True,
            "data": _serialize_discount_rule(rule) if rule else None,
            "message": "Discount rule found" if rule else "No discount rule found",
        }
    except Exception as e:
        frappe.log_error(f"Error getting inventory discount for item: {str(e)}", "Get Inventory Discount For Item Error")
        return {
            "success": False,
            "message": f"Error getting inventory discount for item: {str(e)}",
        }


@frappe.whitelist()
def bulk_get_inventory_discounts(
    items: Union[str, List[Dict]],
    company: str,
    warehouse: str = None,
    posting_date: str = None,
) -> Dict:
    """
    Return applicable discount rules for multiple items in one call.
    Accepts per-row overrides for warehouse, batch_no, and item_group.
    """
    try:
        if isinstance(items, str):
            items = json.loads(items)

        if not isinstance(items, list):
            frappe.throw(_("items must be a list"), frappe.ValidationError)
        if not company:
            frappe.throw(_("company is required"), frappe.ValidationError)

        results = []
        for row in items:
            item_code = (row or {}).get("item_code")
            if not item_code:
                frappe.throw(_("item_code is required for each row"), frappe.ValidationError)

            row_item_group = row.get("item_group") or frappe.db.get_value("Item", item_code, "item_group")
            row_warehouse = row.get("warehouse") or warehouse

            rule = get_applicable_inventory_discount(
                item_code=item_code,
                company=company,
                warehouse=row_warehouse,
                batch_no=row.get("batch_no"),
                item_group=row_item_group,
                posting_date=posting_date,
            )

            results.append(
                {
                    "item_code": item_code,
                    "batch_no": row.get("batch_no"),
                    "warehouse": row_warehouse,
                    "item_group": row_item_group,
                    "rule": _serialize_discount_rule(rule) if rule else None,
                }
            )

        return {
            "success": True,
            "data": results,
            "message": "Discount lookup completed",
        }
    except Exception as e:
        frappe.log_error(f"Error getting inventory discounts in bulk: {str(e)}", "Bulk Get Inventory Discounts Error")
        return {
            "success": False,
            "message": f"Error getting inventory discounts: {str(e)}",
        }


@frappe.whitelist()
def list_stock_entries(
    stock_entry_type: str = None,
    company: str = None,
    warehouse: str = None,
    item_code: str = None,
    from_date: str = None,
    to_date: str = None,
    docstatus: int = 1,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    List stock entries with filters.
    
    Args:
        stock_entry_type: Filter by stock entry type (Material Receipt, Material Issue, Material Transfer, etc.)
        company: Company name (optional, uses default if not provided)
        warehouse: Filter by warehouse (checks both source and target warehouses)
        item_code: Filter by item code
        from_date: Start date (optional, format: YYYY-MM-DD)
        to_date: End date (optional, format: YYYY-MM-DD)
        docstatus: Document status (0=Draft, 1=Submitted, 2=Cancelled, default: 1)
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
    
    Returns:
        dict: List of stock entries with pagination
    """
    try:
        # Get company if not provided
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        # Build filters
        filters = {}
        if company:
            filters["company"] = company
        if stock_entry_type:
            filters["stock_entry_type"] = stock_entry_type
        if from_date:
            filters["posting_date"] = [">=", from_date]
        if to_date:
            if "posting_date" in filters:
                filters["posting_date"] = ["between", [from_date or "1900-01-01", to_date]]
            else:
                filters["posting_date"] = ["<=", to_date]
        if docstatus is not None:
            filters["docstatus"] = docstatus
        
        # Get stock entries
        entries = frappe.get_all(
            "Stock Entry",
            filters=filters,
            fields=[
                "name",
                "stock_entry_type",
                "purpose",
                "company",
                "posting_date",
                "posting_time",
                "docstatus",
                "total_outgoing_value",
                "total_incoming_value",
                "total_additional_costs",
                "total_amount",
                "items_count",
            ],
            order_by="posting_date desc, posting_time desc, creation desc",
            limit_page_length=page_size,
            start=(page - 1) * page_size,
        )
        
        # Get total count for pagination
        total = frappe.db.count("Stock Entry", filters=filters)
        
        # If warehouse or item_code filter, need to filter by items
        if warehouse or item_code:
            filtered_entries = []
            for entry in entries:
                # Get items for this stock entry
                item_filters = {"parent": entry["name"]}
                if item_code:
                    item_filters["item_code"] = item_code
                
                items = frappe.get_all(
                    "Stock Entry Detail",
                    filters=item_filters,
                    fields=["item_code", "qty", "s_warehouse", "t_warehouse", "basic_rate", "amount"],
                )
                
                # Filter by warehouse if specified (check both source and target)
                if warehouse:
                    items = [item for item in items if item.get("s_warehouse") == warehouse or item.get("t_warehouse") == warehouse]
                
                if items:
                    entry["items"] = items
                    filtered_entries.append(entry)
            
            entries = filtered_entries
        
        # Get items for each entry if not already fetched
        if not warehouse and not item_code:
            for entry in entries:
                items = frappe.get_all(
                    "Stock Entry Detail",
                    filters={"parent": entry["name"]},
                    fields=["item_code", "qty", "s_warehouse", "t_warehouse", "basic_rate", "amount"],
                )
                entry["items"] = items
        
        return {
            "success": True,
            "data": {
                "entries": entries,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size,
                },
            },
        }
    except Exception as e:
        frappe.log_error(f"Error listing stock entries: {str(e)}", "List Stock Entries Error")
        return {
            "success": False,
            "message": f"Error listing stock entries: {str(e)}",
        }


@frappe.whitelist()
def list_material_receipts(
    company: str = None,
    warehouse: str = None,
    item_code: str = None,
    from_date: str = None,
    to_date: str = None,
    docstatus: int = 1,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    List material receipt stock entries.
    
    Args:
        company: Company name (optional, uses default if not provided)
        warehouse: Filter by target warehouse
        item_code: Filter by item code
        from_date: Start date (optional, format: YYYY-MM-DD)
        to_date: End date (optional, format: YYYY-MM-DD)
        docstatus: Document status (0=Draft, 1=Submitted, 2=Cancelled, default: 1)
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
    
    Returns:
        dict: List of material receipt entries with pagination
    """
    return list_stock_entries(
        stock_entry_type="Material Receipt",
        company=company,
        warehouse=warehouse,
        item_code=item_code,
        from_date=from_date,
        to_date=to_date,
        docstatus=docstatus,
        page=page,
        page_size=page_size,
    )


@frappe.whitelist()
def list_material_issues(
    company: str = None,
    warehouse: str = None,
    item_code: str = None,
    from_date: str = None,
    to_date: str = None,
    docstatus: int = 1,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    List material issue stock entries.
    
    Args:
        company: Company name (optional, uses default if not provided)
        warehouse: Filter by source warehouse
        item_code: Filter by item code
        from_date: Start date (optional, format: YYYY-MM-DD)
        to_date: End date (optional, format: YYYY-MM-DD)
        docstatus: Document status (0=Draft, 1=Submitted, 2=Cancelled, default: 1)
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
    
    Returns:
        dict: List of material issue entries with pagination
    """
    return list_stock_entries(
        stock_entry_type="Material Issue",
        company=company,
        warehouse=warehouse,
        item_code=item_code,
        from_date=from_date,
        to_date=to_date,
        docstatus=docstatus,
        page=page,
        page_size=page_size,
    )


@frappe.whitelist()
def list_material_transfers(
    company: str = None,
    warehouse: str = None,
    item_code: str = None,
    from_date: str = None,
    to_date: str = None,
    docstatus: int = 1,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    List material transfer stock entries.
    
    Args:
        company: Company name (optional, uses default if not provided)
        warehouse: Filter by source or target warehouse
        item_code: Filter by item code
        from_date: Start date (optional, format: YYYY-MM-DD)
        to_date: End date (optional, format: YYYY-MM-DD)
        docstatus: Document status (0=Draft, 1=Submitted, 2=Cancelled, default: 1)
        page: Page number (default: 1)
        page_size: Items per page (default: 20)
    
    Returns:
        dict: List of material transfer entries with pagination
    """
    return list_stock_entries(
        stock_entry_type="Material Transfer",
        company=company,
        warehouse=warehouse,
        item_code=item_code,
        from_date=from_date,
        to_date=to_date,
        docstatus=docstatus,
        page=page,
        page_size=page_size,
    )


@frappe.whitelist()
def get_stock_entry_details(
    stock_entry_name: str,
) -> Dict:
    """
    Get detailed information about a specific stock entry.
    
    Args:
        stock_entry_name: Name of the stock entry document
    
    Returns:
        dict: Detailed stock entry information including all items
    """
    try:
        if not frappe.db.exists("Stock Entry", stock_entry_name):
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' does not exist",
            }
        
        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Get all items
        items = []
        for item in stock_entry.items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "s_warehouse": item.s_warehouse,
                "t_warehouse": item.t_warehouse,
                "basic_rate": item.basic_rate,
                "amount": item.amount,
                "valuation_rate": item.valuation_rate,
                "serial_no": item.serial_no,
                "batch_no": item.batch_no,
                "expense_account": item.expense_account,
                "cost_center": item.cost_center,
            })
        
        return {
            "success": True,
            "data": {
                "name": stock_entry.name,
                "stock_entry_type": stock_entry.stock_entry_type,
                "purpose": stock_entry.purpose,
                "company": stock_entry.company,
                "posting_date": str(stock_entry.posting_date),
                "posting_time": str(stock_entry.posting_time) if stock_entry.posting_time else None,
                "docstatus": stock_entry.docstatus,
                "total_outgoing_value": stock_entry.total_outgoing_value,
                "total_incoming_value": stock_entry.total_incoming_value,
                "total_additional_costs": stock_entry.total_additional_costs,
                "total_amount": stock_entry.total_amount,
                "items": items,
                "items_count": len(items),
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting stock entry details: {str(e)}", "Get Stock Entry Details Error")
        return {
            "success": False,
            "message": f"Error getting stock entry details: {str(e)}",
        }


@frappe.whitelist()
def update_stock_entry(
    stock_entry_name: str,
    items: Union[str, List[Dict]] = None,
    posting_date: str = None,
    posting_time: str = None,
    from_warehouse: str = None,
    to_warehouse: str = None,
    do_not_submit: bool = False,
) -> Dict:
    """
    Update an existing stock entry (only works for draft entries).
    
    Args:
        stock_entry_name: Name of the stock entry to update
        items: JSON string or list of items to update (optional)
        posting_date: Updated posting date (optional)
        posting_time: Updated posting time (optional)
        from_warehouse: Updated source warehouse (optional)
        to_warehouse: Updated target warehouse (optional)
        do_not_submit: If True, don't submit after update (default: False)
    
    Returns:
        dict: Updated stock entry details
    """
    try:
        if not frappe.db.exists("Stock Entry", stock_entry_name):
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' does not exist",
            }
        
        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Check if document is draft
        if stock_entry.docstatus != 0:
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' cannot be updated. Only draft entries (docstatus=0) can be updated. Current status: {stock_entry.docstatus}",
                "docstatus": stock_entry.docstatus,
            }
        
        # Update posting date
        if posting_date:
            stock_entry.posting_date = posting_date
            stock_entry.set_posting_time = 1
        
        # Update posting time
        if posting_time:
            stock_entry.posting_time = posting_time
        
        # Update document-level warehouses
        if from_warehouse:
            stock_entry.from_warehouse = from_warehouse
        if to_warehouse:
            stock_entry.to_warehouse = to_warehouse
        
        # Update items if provided
        if items is not None:
            # Parse items
            if isinstance(items, str):
                items = json.loads(items)
            
            if not isinstance(items, list):
                return {
                    "success": False,
                    "message": "Items must be a list",
                }
            
            # Clear existing items
            stock_entry.items = []
            
            # Add new items
            for item in items:
                item_code = item.get("item_code")
                if not item_code:
                    return {
                        "success": False,
                        "message": "item_code is required for all items",
                    }
                
                # Validate item exists
                if not frappe.db.exists("Item", item_code):
                    return {
                        "success": False,
                        "message": f"Item '{item_code}' does not exist",
                    }
                
                qty = flt(item.get("qty", 0))
                if qty <= 0:
                    return {
                        "success": False,
                        "message": f"Quantity must be greater than 0 for item '{item_code}'",
                    }
                
                s_warehouse = item.get("s_warehouse") or from_warehouse
                t_warehouse = item.get("t_warehouse") or to_warehouse
                
                # Validate warehouses
                if s_warehouse and not frappe.db.exists("Warehouse", s_warehouse):
                    return {
                        "success": False,
                        "message": f"Source warehouse '{s_warehouse}' does not exist",
                    }
                
                if t_warehouse and not frappe.db.exists("Warehouse", t_warehouse):
                    return {
                        "success": False,
                        "message": f"Target warehouse '{t_warehouse}' does not exist",
                    }
                
                stock_entry.append("items", {
                    "item_code": item_code,
                    "qty": qty,
                    "s_warehouse": s_warehouse,
                    "t_warehouse": t_warehouse,
                    "basic_rate": item.get("basic_rate"),
                    "conversion_factor": item.get("conversion_factor", 1.0),
                    "serial_no": item.get("serial_no"),
                    "batch_no": item.get("batch_no"),
                    "expense_account": item.get("expense_account"),
                    "cost_center": item.get("cost_center"),
                })
        
        # Validate and save
        stock_entry.validate()
        stock_entry.save(ignore_permissions=True)
        
        # Submit if requested
        if not do_not_submit:
            stock_entry.submit()
        
        return {
            "success": True,
            "message": "Stock entry updated successfully",
            "data": {
                "name": stock_entry.name,
                "stock_entry_type": stock_entry.stock_entry_type,
                "company": stock_entry.company,
                "posting_date": str(stock_entry.posting_date),
                "docstatus": stock_entry.docstatus,
                "items_count": len(stock_entry.items),
            },
        }
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error updating stock entry: {str(e)}", "Update Stock Entry Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error updating stock entry: {str(e)}", "Update Stock Entry Error")
        return {
            "success": False,
            "message": f"Error updating stock entry: {str(e)}",
        }


@frappe.whitelist()
def cancel_stock_entry(
    stock_entry_name: str,
    reason: str = None,
) -> Dict:
    """
    Cancel a submitted stock entry.
    
    Args:
        stock_entry_name: Name of the stock entry to cancel
        reason: Reason for cancellation (optional)
    
    Returns:
        dict: Cancellation result
    """
    try:
        if not frappe.db.exists("Stock Entry", stock_entry_name):
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' does not exist",
            }
        
        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Check if document is submitted
        if stock_entry.docstatus != 1:
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' cannot be cancelled. Only submitted entries (docstatus=1) can be cancelled. Current status: {stock_entry.docstatus}",
                "docstatus": stock_entry.docstatus,
            }
        
        # Add reason if provided
        if reason:
            stock_entry.add_comment("Comment", f"Cancellation reason: {reason}")
        
        # Cancel the document
        stock_entry.cancel()
        
        return {
            "success": True,
            "message": "Stock entry cancelled successfully",
            "data": {
                "name": stock_entry.name,
                "docstatus": stock_entry.docstatus,
                "cancelled_at": str(frappe.utils.now()),
            },
        }
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error cancelling stock entry: {str(e)}", "Cancel Stock Entry Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error cancelling stock entry: {str(e)}", "Cancel Stock Entry Error")
        return {
            "success": False,
            "message": f"Error cancelling stock entry: {str(e)}",
        }


@frappe.whitelist()
def submit_stock_entry(
    stock_entry_name: str,
) -> Dict:
    """
    Submit a draft stock entry.
    
    Args:
        stock_entry_name: Name of the stock entry to submit
    
    Returns:
        dict: Submission result
    """
    try:
        if not frappe.db.exists("Stock Entry", stock_entry_name):
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' does not exist",
            }
        
        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Check if document is draft
        if stock_entry.docstatus != 0:
            return {
                "success": False,
                "message": f"Stock Entry '{stock_entry_name}' cannot be submitted. Only draft entries (docstatus=0) can be submitted. Current status: {stock_entry.docstatus}",
                "docstatus": stock_entry.docstatus,
            }
        
        # Submit the document
        stock_entry.submit()
        
        return {
            "success": True,
            "message": "Stock entry submitted successfully",
            "data": {
                "name": stock_entry.name,
                "stock_entry_type": stock_entry.stock_entry_type,
                "company": stock_entry.company,
                "posting_date": str(stock_entry.posting_date),
                "docstatus": stock_entry.docstatus,
                "items_count": len(stock_entry.items),
            },
        }
    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error submitting stock entry: {str(e)}", "Submit Stock Entry Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error submitting stock entry: {str(e)}", "Submit Stock Entry Error")
        return {
            "success": False,
            "message": f"Error submitting stock entry: {str(e)}",
        }

