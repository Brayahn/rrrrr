"""
Dashboard Metrics API
Provides comprehensive dashboard metrics for POS system with filtering by staff and warehouse
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate, add_days, add_months, get_first_day, get_last_day
from frappe.query_builder import DocType, functions as fn


def _get_default_company() -> Optional[str]:
    """Get the default company for the current user."""
    company = frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.db.get_default("company")
    return company


def _build_base_filters(
    company: Optional[str] = None,
    warehouse: Optional[str] = None,
    staff: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> tuple:
    """Build base filters for queries."""
    filters = {}
    
    if company:
        filters["company"] = company
    else:
        company = _get_default_company()
        if company:
            filters["company"] = company
    
    if from_date and to_date:
        filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["posting_date"] = [">=", from_date]
    elif to_date:
        filters["posting_date"] = ["<=", to_date]
    
    if staff:
        filters["owner"] = staff
    
    return filters, company


def _get_warehouse_filter(warehouse: Optional[str] = None) -> Dict:
    """Get warehouse filter for item-level queries."""
    warehouse_filter = {}
    if warehouse:
        warehouse_filter["warehouse"] = warehouse
    return warehouse_filter


@frappe.whitelist()
def get_dashboard_metrics(
    company: Optional[str] = None,
    warehouse: Optional[str] = None,
    staff: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    period: str = "30days",  # "30days", "month", "year", "custom"
) -> Dict:
    """
    Get comprehensive dashboard metrics with filtering by staff and warehouse.
    
    Args:
        company: Company name (optional, uses default if not provided)
        warehouse: Warehouse name to filter by (optional)
        staff: User/Staff name to filter by (optional)
        from_date: Start date for custom period (YYYY-MM-DD)
        to_date: End date for custom period (YYYY-MM-DD)
        period: Time period - "30days", "month", "year", or "custom"
    
    Returns:
        dict: Complete dashboard metrics
    """
    try:
        # Set date range based on period
        if period == "30days":
            to_date = to_date or nowdate()
            from_date = from_date or str(add_days(getdate(to_date), -30))
        elif period == "month":
            to_date = to_date or nowdate()
            from_date = from_date or str(get_first_day(to_date))
            to_date = str(get_last_day(to_date))
        elif period == "year":
            to_date = to_date or nowdate()
            from_date = from_date or str(get_first_day(to_date, "year"))
            to_date = str(get_last_day(to_date, "year"))
        # "custom" uses provided from_date and to_date
        
        filters, company = _build_base_filters(company, warehouse, staff, from_date, to_date)
        warehouse_filter = _get_warehouse_filter(warehouse)
        
        # Get all metrics
        stats = _get_sales_stats(filters, warehouse_filter, company)
        stats.update(_get_purchase_stats(filters, warehouse_filter, company))
        stats.update(_get_financial_stats(filters, company))
        stats.update(_get_additional_metrics(filters, warehouse_filter, company))
        
        # Get time series data
        sales_last_30_days = _get_daily_sales_data(filters, warehouse_filter, company)
        monthly_sales = _get_monthly_sales_data(filters, warehouse_filter, company)
        
        # Get detailed lists
        sales_due = _get_sales_due(filters, company)
        purchases_due = _get_purchases_due(filters, company)
        stock_alerts = _get_stock_alerts(warehouse_filter, company)
        pending_shipments = _get_pending_shipments(filters, company)
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "salesLast30Days": sales_last_30_days,
                "monthlySales": monthly_sales,
                "salesDue": sales_due,
                "purchasesDue": purchases_due,
                "stockAlerts": stock_alerts,
                "pendingShipments": pending_shipments,
            },
            "filters": {
                "company": company,
                "warehouse": warehouse,
                "staff": staff,
                "from_date": from_date,
                "to_date": to_date,
                "period": period,
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting dashboard metrics: {str(e)}", "Dashboard Metrics Error")
        return {
            "success": False,
            "message": f"Error getting dashboard metrics: {str(e)}",
        }


def _get_sales_stats(filters: Dict, warehouse_filter: Dict, company: str) -> Dict:
    """Get sales statistics from both Sales Invoice and POS Invoice."""
    SalesInvoice = DocType("Sales Invoice")
    SalesInvoiceItem = DocType("Sales Invoice Item")
    POSInvoice = DocType("POS Invoice")
    POSInvoiceItem = DocType("POS Invoice Item")
    
    # Helper function to apply common filters to invoice query
    def apply_invoice_filters(query, Invoice):
        if filters.get("company"):
            query = query.where(Invoice.company == filters["company"])
        if filters.get("owner"):
            query = query.where(Invoice.owner == filters["owner"])
        if filters.get("posting_date"):
            if isinstance(filters["posting_date"], list):
                if filters["posting_date"][0] == ">=":
                    query = query.where(Invoice.posting_date >= filters["posting_date"][1])
                elif filters["posting_date"][0] == "<=":
                    query = query.where(Invoice.posting_date <= filters["posting_date"][1])
                elif filters["posting_date"][0] == "between":
                    query = query.where(
                        Invoice.posting_date.between(
                            filters["posting_date"][1][0],
                            filters["posting_date"][1][1]
                        )
                    )
            else:
                query = query.where(Invoice.posting_date >= filters["posting_date"])
        return query
    
    # Query Sales Invoices
    si_base_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 0)
    )
    si_base_query = apply_invoice_filters(si_base_query, SalesInvoice)
    
    # Query POS Invoices
    pos_base_query = (
        frappe.qb.from_(POSInvoice)
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 0)
    )
    pos_base_query = apply_invoice_filters(pos_base_query, POSInvoice)
    
    # Total Sales (gross) - sum from both Sales Invoice and POS Invoice
    si_total = (
        si_base_query.select(fn.Sum(SalesInvoice.grand_total).as_("total"))
        .run(as_dict=True)
    )
    pos_total = (
        pos_base_query.select(fn.Sum(POSInvoice.grand_total).as_("total"))
        .run(as_dict=True)
    )
    total_sales = flt(si_total[0].get("total") if si_total and si_total[0].get("total") else 0.0) + \
                  flt(pos_total[0].get("total") if pos_total and pos_total[0].get("total") else 0.0)
    
    # Net Sales (after returns) - sum from both
    si_net = (
        si_base_query.select(fn.Sum(SalesInvoice.base_net_total).as_("total"))
        .run(as_dict=True)
    )
    pos_net = (
        pos_base_query.select(fn.Sum(POSInvoice.base_net_total).as_("total"))
        .run(as_dict=True)
    )
    net_sales = flt(si_net[0].get("total") if si_net and si_net[0].get("total") else 0.0) + \
                flt(pos_net[0].get("total") if pos_net and pos_net[0].get("total") else 0.0)
    
    # Sales Returns - from both Sales Invoice and POS Invoice
    si_returns_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 1)
    )
    si_returns_query = apply_invoice_filters(si_returns_query, SalesInvoice)
    
    pos_returns_query = (
        frappe.qb.from_(POSInvoice)
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 1)
    )
    pos_returns_query = apply_invoice_filters(pos_returns_query, POSInvoice)
    
    si_returns = (
        si_returns_query
        .select(fn.Sum(fn.Abs(SalesInvoice.grand_total)).as_("total"))
        .run(as_dict=True)
    )
    pos_returns = (
        pos_returns_query
        .select(fn.Sum(fn.Abs(POSInvoice.grand_total)).as_("total"))
        .run(as_dict=True)
    )
    sales_returns = flt(si_returns[0].get("total") if si_returns and si_returns[0].get("total") else 0.0) + \
                    flt(pos_returns[0].get("total") if pos_returns and pos_returns[0].get("total") else 0.0)
    
    # Sales Returns Count
    si_returns_count = (
        si_returns_query
        .select(fn.Count(SalesInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    pos_returns_count = (
        pos_returns_query
        .select(fn.Count(POSInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    sales_returns_count = int(si_returns_count[0].get("count") if si_returns_count and si_returns_count[0].get("count") else 0) + \
                          int(pos_returns_count[0].get("count") if pos_returns_count and pos_returns_count[0].get("count") else 0)
    
    # If warehouse filter, sum item amounts from that warehouse only
    # This ensures we only count sales from items in the specified warehouse
    if warehouse_filter.get("warehouse"):
        # Sales Invoice items with warehouse filter
        si_items_with_warehouse = (
            frappe.qb.from_(SalesInvoice)
            .join(SalesInvoiceItem)
            .on(SalesInvoice.name == SalesInvoiceItem.parent)
            .where(SalesInvoice.docstatus == 1)
            .where(SalesInvoice.is_return == 0)
            .where(SalesInvoiceItem.warehouse == warehouse_filter["warehouse"])
        )
        si_items_with_warehouse = apply_invoice_filters(si_items_with_warehouse, SalesInvoice)
        
        # POS Invoice items with warehouse filter
        pos_items_with_warehouse = (
            frappe.qb.from_(POSInvoice)
            .join(POSInvoiceItem)
            .on(POSInvoice.name == POSInvoiceItem.parent)
            .where(POSInvoice.docstatus == 1)
            .where(POSInvoice.is_return == 0)
            .where(POSInvoiceItem.warehouse == warehouse_filter["warehouse"])
        )
        pos_items_with_warehouse = apply_invoice_filters(pos_items_with_warehouse, POSInvoice)
        
        # Sum base_amount (includes item-level taxes) for total sales
        si_total_result = (
            si_items_with_warehouse
            .select(fn.Sum(SalesInvoiceItem.base_amount).as_("total"))
            .run(as_dict=True)
        )
        pos_total_result = (
            pos_items_with_warehouse
            .select(fn.Sum(POSInvoiceItem.base_amount).as_("total"))
            .run(as_dict=True)
        )
        total_sales = flt(si_total_result[0].get("total") if si_total_result and si_total_result[0].get("total") else 0.0) + \
                      flt(pos_total_result[0].get("total") if pos_total_result and pos_total_result[0].get("total") else 0.0)
        
        # Sum base_net_amount (net amount after item discounts) for net sales
        si_net_result = (
            si_items_with_warehouse
            .select(fn.Sum(SalesInvoiceItem.base_net_amount).as_("total"))
            .run(as_dict=True)
        )
        pos_net_result = (
            pos_items_with_warehouse
            .select(fn.Sum(POSInvoiceItem.base_net_amount).as_("total"))
            .run(as_dict=True)
        )
        net_sales = flt(si_net_result[0].get("total") if si_net_result and si_net_result[0].get("total") else 0.0) + \
                    flt(pos_net_result[0].get("total") if pos_net_result and pos_net_result[0].get("total") else 0.0)
    
    return {
        "totalSales": total_sales,
        "netSales": net_sales,
        "salesReturns": sales_returns,
        "salesReturnsCount": sales_returns_count,
    }


def _get_purchase_stats(filters: Dict, warehouse_filter: Dict, company: str) -> Dict:
    """Get purchase statistics."""
    PurchaseInvoice = DocType("Purchase Invoice")
    PurchaseInvoiceItem = DocType("Purchase Invoice Item")
    
    # Base query for purchase invoices
    base_query = (
        frappe.qb.from_(PurchaseInvoice)
        .where(PurchaseInvoice.docstatus == 1)
        .where(PurchaseInvoice.is_return == 0)
    )
    
    # Apply filters
    if filters.get("company"):
        base_query = base_query.where(PurchaseInvoice.company == filters["company"])
    if filters.get("owner"):
        base_query = base_query.where(PurchaseInvoice.owner == filters["owner"])
    if filters.get("posting_date"):
        if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
            base_query = base_query.where(
                PurchaseInvoice.posting_date.between(
                    filters["posting_date"][1][0],
                    filters["posting_date"][1][1]
                )
            )
    
    # Total Purchases
    total_purchases_result = (
        base_query.select(fn.Sum(PurchaseInvoice.grand_total).as_("total"))
        .run(as_dict=True)
    )
    total_purchases = flt(total_purchases_result[0].get("total")) if total_purchases_result and total_purchases_result[0].get("total") else 0.0
    
    # Net Purchases
    net_purchases_result = (
        base_query.select(fn.Sum(PurchaseInvoice.base_net_total).as_("total"))
        .run(as_dict=True)
    )
    net_purchases = flt(net_purchases_result[0].get("total")) if net_purchases_result and net_purchases_result[0].get("total") else 0.0
    
    # Purchase Returns
    returns_query = (
        frappe.qb.from_(PurchaseInvoice)
        .where(PurchaseInvoice.docstatus == 1)
        .where(PurchaseInvoice.is_return == 1)
    )
    
    if filters.get("company"):
        returns_query = returns_query.where(PurchaseInvoice.company == filters["company"])
    if filters.get("owner"):
        returns_query = returns_query.where(PurchaseInvoice.owner == filters["owner"])
    if filters.get("posting_date"):
        if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
            returns_query = returns_query.where(
                PurchaseInvoice.posting_date.between(
                    filters["posting_date"][1][0],
                    filters["posting_date"][1][1]
                )
            )
    
    returns_result = (
        returns_query
        .select(fn.Sum(fn.Abs(PurchaseInvoice.grand_total)).as_("total"))
        .run(as_dict=True)
    )
    purchase_returns = flt(returns_result[0].get("total")) if returns_result and returns_result[0].get("total") else 0.0
    
    # Purchase Returns Count
    returns_count_result = (
        returns_query
        .select(fn.Count(PurchaseInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    purchase_returns_count = int(returns_count_result[0].get("count")) if returns_count_result and returns_count_result[0].get("count") else 0
    
    # If warehouse filter, sum item amounts from that warehouse only
    # This ensures we only count purchases from items in the specified warehouse
    if warehouse_filter.get("warehouse"):
        # Sum item amounts from items in the specified warehouse
        items_with_warehouse = (
            frappe.qb.from_(PurchaseInvoice)
            .join(PurchaseInvoiceItem)
            .on(PurchaseInvoice.name == PurchaseInvoiceItem.parent)
            .where(PurchaseInvoice.docstatus == 1)
            .where(PurchaseInvoice.is_return == 0)
            .where(PurchaseInvoiceItem.warehouse == warehouse_filter["warehouse"])
        )
        
        if filters.get("company"):
            items_with_warehouse = items_with_warehouse.where(PurchaseInvoice.company == filters["company"])
        if filters.get("owner"):
            items_with_warehouse = items_with_warehouse.where(PurchaseInvoice.owner == filters["owner"])
        if filters.get("posting_date"):
            if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
                items_with_warehouse = items_with_warehouse.where(
                    PurchaseInvoice.posting_date.between(
                        filters["posting_date"][1][0],
                        filters["posting_date"][1][1]
                    )
                )
        
        # Sum base_amount (includes item-level taxes) for total purchases
        # Note: This doesn't include invoice-level taxes proportionally, but is the most accurate for warehouse filtering
        total_purchases_result = (
            items_with_warehouse
            .select(fn.Sum(PurchaseInvoiceItem.base_amount).as_("total"))
            .run(as_dict=True)
        )
        total_purchases = flt(total_purchases_result[0].get("total")) if total_purchases_result and total_purchases_result[0].get("total") else 0.0
        
        # Sum base_net_amount (net amount after item discounts) for net purchases
        net_purchases_result = (
            items_with_warehouse
            .select(fn.Sum(PurchaseInvoiceItem.base_net_amount).as_("total"))
            .run(as_dict=True)
        )
        net_purchases = flt(net_purchases_result[0].get("total")) if net_purchases_result and net_purchases_result[0].get("total") else 0.0
    
    return {
        "totalPurchases": total_purchases,
        "netPurchases": net_purchases,
        "purchaseReturns": purchase_returns,
        "purchaseReturnsCount": purchase_returns_count,
    }


def _get_financial_stats(filters: Dict, company: str) -> Dict:
    """Get financial statistics (outstanding invoices, expenses)."""
    SalesInvoice = DocType("Sales Invoice")
    PurchaseInvoice = DocType("Purchase Invoice")
    JournalEntry = DocType("Journal Entry")
    JournalEntryAccount = DocType("Journal Entry Account")
    
    # Outstanding Sales Invoices
    outstanding_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.outstanding_amount > 0)
    )
    
    if filters.get("company"):
        outstanding_query = outstanding_query.where(SalesInvoice.company == filters["company"])
    if filters.get("owner"):
        outstanding_query = outstanding_query.where(SalesInvoice.owner == filters["owner"])
    
    outstanding_result = (
        outstanding_query
        .select(fn.Sum(SalesInvoice.outstanding_amount).as_("total"))
        .run(as_dict=True)
    )
    invoices_due = flt(outstanding_result[0].get("total")) if outstanding_result and outstanding_result[0].get("total") else 0.0
    
    # Outstanding Invoices Count
    count_result = (
        outstanding_query
        .select(fn.Count(SalesInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    invoices_due_count = int(count_result[0].get("count")) if count_result and count_result[0].get("count") else 0
    
    # Total Expenses (from Journal Entries - expense accounts)
    # This is a simplified calculation - you may want to refine this
    expense_query = (
        frappe.qb.from_(JournalEntry)
        .join(JournalEntryAccount)
        .on(JournalEntry.name == JournalEntryAccount.parent)
        .where(JournalEntry.docstatus == 1)
        .where(JournalEntryAccount.account_type == "Expense")
    )
    
    if filters.get("company"):
        expense_query = expense_query.where(JournalEntry.company == filters["company"])
    if filters.get("posting_date"):
        if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
            expense_query = expense_query.where(
                JournalEntry.posting_date.between(
                    filters["posting_date"][1][0],
                    filters["posting_date"][1][1]
                )
            )
    
    expense_result = (
        expense_query
        .select(fn.Sum(JournalEntryAccount.debit - JournalEntryAccount.credit).as_("total"))
        .run(as_dict=True)
    )
    total_expense = flt(expense_result[0].get("total")) if expense_result and expense_result[0].get("total") else 0.0
    
    return {
        "invoicesDue": invoices_due,
        "invoicesDueCount": invoices_due_count,
        "totalExpense": total_expense,
    }


def _get_additional_metrics(filters: Dict, warehouse_filter: Dict, company: str) -> Dict:
    """Get additional metrics like profit margin and average transaction from both Sales Invoice and POS Invoice."""
    SalesInvoice = DocType("Sales Invoice")
    SalesInvoiceItem = DocType("Sales Invoice Item")
    POSInvoice = DocType("POS Invoice")
    POSInvoiceItem = DocType("POS Invoice Item")
    
    # Helper function to apply filters
    def apply_filters(query, Invoice):
        if filters.get("company"):
            query = query.where(Invoice.company == filters["company"])
        if filters.get("owner"):
            query = query.where(Invoice.owner == filters["owner"])
        if filters.get("posting_date"):
            if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
                query = query.where(
                    Invoice.posting_date.between(
                        filters["posting_date"][1][0],
                        filters["posting_date"][1][1]
                    )
                )
        return query
    
    # Base queries for Sales Invoice and POS Invoice
    si_base_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 0)
    )
    si_base_query = apply_filters(si_base_query, SalesInvoice)
    
    pos_base_query = (
        frappe.qb.from_(POSInvoice)
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 0)
    )
    pos_base_query = apply_filters(pos_base_query, POSInvoice)
    
    # Average Transaction Value - weighted average from both
    si_avg_result = (
        si_base_query
        .select(fn.Avg(SalesInvoice.grand_total).as_("avg"), fn.Count(SalesInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    pos_avg_result = (
        pos_base_query
        .select(fn.Avg(POSInvoice.grand_total).as_("avg"), fn.Count(POSInvoice.name).as_("count"))
        .run(as_dict=True)
    )
    
    si_avg = flt(si_avg_result[0].get("avg")) if si_avg_result and si_avg_result[0].get("avg") else 0.0
    pos_avg = flt(pos_avg_result[0].get("avg")) if pos_avg_result and pos_avg_result[0].get("avg") else 0.0
    si_count = flt(si_avg_result[0].get("count")) if si_avg_result and si_avg_result[0].get("count") else 0
    pos_count = flt(pos_avg_result[0].get("count")) if pos_avg_result and pos_avg_result[0].get("count") else 0
    
    # Calculate weighted average
    total_count = si_count + pos_count
    if total_count > 0:
        average_transaction = ((si_avg * si_count) + (pos_avg * pos_count)) / total_count
    else:
        average_transaction = 0.0
    
    # Net Sales from both
    si_net_result = (
        si_base_query
        .select(fn.Sum(SalesInvoice.base_net_total).as_("total"))
        .run(as_dict=True)
    )
    pos_net_result = (
        pos_base_query
        .select(fn.Sum(POSInvoice.base_net_total).as_("total"))
        .run(as_dict=True)
    )
    net_sales = flt(si_net_result[0].get("total") if si_net_result and si_net_result[0].get("total") else 0.0) + \
                flt(pos_net_result[0].get("total") if pos_net_result and pos_net_result[0].get("total") else 0.0)
    
    # Get total cost from items - from both Sales Invoice and POS Invoice
    # For Sales Invoice, use incoming_rate field
    si_cost_query = (
        frappe.qb.from_(SalesInvoice)
        .join(SalesInvoiceItem)
        .on(SalesInvoice.name == SalesInvoiceItem.parent)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 0)
    )
    si_cost_query = apply_filters(si_cost_query, SalesInvoice)
    if warehouse_filter.get("warehouse"):
        si_cost_query = si_cost_query.where(SalesInvoiceItem.warehouse == warehouse_filter["warehouse"])
    
    si_cost_result = (
        si_cost_query
        .select(fn.Sum(SalesInvoiceItem.incoming_rate * SalesInvoiceItem.qty).as_("total"))
        .run(as_dict=True)
    )
    si_cost = flt(si_cost_result[0].get("total") if si_cost_result and si_cost_result[0].get("total") else 0.0)
    
    # For POS Invoice, get cost from Stock Ledger Entry
    # For sales transactions, cost = abs(stock_value_difference / actual_qty) * qty
    # Since actual_qty is negative for sales, ABS gives us the positive cost rate
    StockLedgerEntry = DocType("Stock Ledger Entry")
    pos_cost_query = (
        frappe.qb.from_(POSInvoice)
        .join(POSInvoiceItem)
        .on(POSInvoice.name == POSInvoiceItem.parent)
        .join(StockLedgerEntry)
        .on(
            (StockLedgerEntry.voucher_type == "POS Invoice")
            & (StockLedgerEntry.voucher_no == POSInvoice.name)
            & (StockLedgerEntry.voucher_detail_no == POSInvoiceItem.name)
            & (StockLedgerEntry.item_code == POSInvoiceItem.item_code)
        )
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 0)
        .where(StockLedgerEntry.is_cancelled == 0)
        .where(StockLedgerEntry.actual_qty != 0)  # Exclude zero qty entries
    )
    pos_cost_query = apply_filters(pos_cost_query, POSInvoice)
    if warehouse_filter.get("warehouse"):
        pos_cost_query = pos_cost_query.where(POSInvoiceItem.warehouse == warehouse_filter["warehouse"])
        pos_cost_query = pos_cost_query.where(StockLedgerEntry.warehouse == warehouse_filter["warehouse"])
    
    # Calculate cost: abs(stock_value_difference / actual_qty) gives the cost per unit (outgoing rate)
    # For sales (actual_qty < 0), stock_value_difference is negative, so ABS gives us positive cost
    # Multiply by POSInvoiceItem.qty to get total cost for that line item
    pos_cost_result = (
        pos_cost_query
        .select(
            fn.Sum(
                fn.Abs(StockLedgerEntry.stock_value_difference / StockLedgerEntry.actual_qty) * POSInvoiceItem.qty
            ).as_("total")
        )
        .run(as_dict=True)
    )
    pos_cost = flt(pos_cost_result[0].get("total") if pos_cost_result and pos_cost_result[0].get("total") else 0.0)
    
    total_cost = si_cost + pos_cost
    
    # Calculate profit margin
    profit_margin = 0.0
    if net_sales > 0:
        profit = net_sales - total_cost
        profit_margin = (profit / net_sales) * 100 if net_sales > 0 else 0.0
    
    return {
        "profitMargin": round(profit_margin, 2),
        "averageTransaction": round(average_transaction, 2),
    }


def _get_daily_sales_data(filters: Dict, warehouse_filter: Dict, company: str) -> List[Dict]:
    """Get daily sales data for last 30 days from both Sales Invoice and POS Invoice."""
    SalesInvoice = DocType("Sales Invoice")
    SalesInvoiceItem = DocType("Sales Invoice Item")
    POSInvoice = DocType("POS Invoice")
    POSInvoiceItem = DocType("POS Invoice Item")
    
    # Get last 30 days
    if filters.get("posting_date") and isinstance(filters["posting_date"], list):
        if filters["posting_date"][0] == "between":
            end_date = getdate(filters["posting_date"][1][1])
            start_date = getdate(filters["posting_date"][1][0])
        elif filters["posting_date"][0] == "<=":
            end_date = getdate(filters["posting_date"][1])
            start_date = add_days(end_date, -30)
        else:
            end_date = nowdate()
            start_date = add_days(end_date, -30)
    else:
        end_date = nowdate()
        start_date = add_days(end_date, -30)
    
    # Get Sales Invoice sales by date
    if warehouse_filter.get("warehouse"):
        si_sales_query = (
            frappe.qb.from_(SalesInvoice)
            .join(SalesInvoiceItem)
            .on(SalesInvoice.name == SalesInvoiceItem.parent)
            .where(SalesInvoice.docstatus == 1)
            .where(SalesInvoice.is_return == 0)
            .where(SalesInvoiceItem.warehouse == warehouse_filter["warehouse"])
            .where(SalesInvoice.posting_date.between(start_date, end_date))
        )
        if filters.get("company"):
            si_sales_query = si_sales_query.where(SalesInvoice.company == filters["company"])
        if filters.get("owner"):
            si_sales_query = si_sales_query.where(SalesInvoice.owner == filters["owner"])
        si_sales_data = (
            si_sales_query
            .select(
                SalesInvoice.posting_date.as_("date"),
                fn.Sum(SalesInvoiceItem.base_amount).as_("sales")
            )
            .groupby(SalesInvoice.posting_date)
            .run(as_dict=True)
        )
    else:
        si_sales_query = (
            frappe.qb.from_(SalesInvoice)
            .where(SalesInvoice.docstatus == 1)
            .where(SalesInvoice.is_return == 0)
            .where(SalesInvoice.posting_date.between(start_date, end_date))
        )
        if filters.get("company"):
            si_sales_query = si_sales_query.where(SalesInvoice.company == filters["company"])
        if filters.get("owner"):
            si_sales_query = si_sales_query.where(SalesInvoice.owner == filters["owner"])
        si_sales_data = (
            si_sales_query
            .select(
                SalesInvoice.posting_date.as_("date"),
                fn.Sum(SalesInvoice.grand_total).as_("sales")
            )
            .groupby(SalesInvoice.posting_date)
            .run(as_dict=True)
        )
    
    # Get POS Invoice sales by date
    if warehouse_filter.get("warehouse"):
        pos_sales_query = (
            frappe.qb.from_(POSInvoice)
            .join(POSInvoiceItem)
            .on(POSInvoice.name == POSInvoiceItem.parent)
            .where(POSInvoice.docstatus == 1)
            .where(POSInvoice.is_return == 0)
            .where(POSInvoiceItem.warehouse == warehouse_filter["warehouse"])
            .where(POSInvoice.posting_date.between(start_date, end_date))
        )
        if filters.get("company"):
            pos_sales_query = pos_sales_query.where(POSInvoice.company == filters["company"])
        if filters.get("owner"):
            pos_sales_query = pos_sales_query.where(POSInvoice.owner == filters["owner"])
        pos_sales_data = (
            pos_sales_query
            .select(
                POSInvoice.posting_date.as_("date"),
                fn.Sum(POSInvoiceItem.base_amount).as_("sales")
            )
            .groupby(POSInvoice.posting_date)
            .run(as_dict=True)
        )
    else:
        pos_sales_query = (
            frappe.qb.from_(POSInvoice)
            .where(POSInvoice.docstatus == 1)
            .where(POSInvoice.is_return == 0)
            .where(POSInvoice.posting_date.between(start_date, end_date))
        )
        if filters.get("company"):
            pos_sales_query = pos_sales_query.where(POSInvoice.company == filters["company"])
        if filters.get("owner"):
            pos_sales_query = pos_sales_query.where(POSInvoice.owner == filters["owner"])
        pos_sales_data = (
            pos_sales_query
            .select(
                POSInvoice.posting_date.as_("date"),
                fn.Sum(POSInvoice.grand_total).as_("sales")
            )
            .groupby(POSInvoice.posting_date)
            .run(as_dict=True)
        )
    
    # Get returns by date from both
    si_returns_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 1)
        .where(SalesInvoice.posting_date.between(start_date, end_date))
    )
    pos_returns_query = (
        frappe.qb.from_(POSInvoice)
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 1)
        .where(POSInvoice.posting_date.between(start_date, end_date))
    )
    
    if filters.get("company"):
        si_returns_query = si_returns_query.where(SalesInvoice.company == filters["company"])
        pos_returns_query = pos_returns_query.where(POSInvoice.company == filters["company"])
    if filters.get("owner"):
        si_returns_query = si_returns_query.where(SalesInvoice.owner == filters["owner"])
        pos_returns_query = pos_returns_query.where(POSInvoice.owner == filters["owner"])
    
    si_returns_data = (
        si_returns_query
        .select(
            SalesInvoice.posting_date.as_("date"),
            fn.Sum(fn.Abs(SalesInvoice.grand_total)).as_("returns")
        )
        .groupby(SalesInvoice.posting_date)
        .run(as_dict=True)
    )
    pos_returns_data = (
        pos_returns_query
        .select(
            POSInvoice.posting_date.as_("date"),
            fn.Sum(fn.Abs(POSInvoice.grand_total)).as_("returns")
        )
        .groupby(POSInvoice.posting_date)
        .run(as_dict=True)
    )
    
    # Combine data from both Sales Invoice and POS Invoice
    sales_dict = defaultdict(float)
    returns_dict = defaultdict(float)
    
    for item in si_sales_data:
        sales_dict[str(item["date"])] += flt(item.get("sales", 0))
    for item in pos_sales_data:
        sales_dict[str(item["date"])] += flt(item.get("sales", 0))
    
    for item in si_returns_data:
        returns_dict[str(item["date"])] += flt(item.get("returns", 0))
    for item in pos_returns_data:
        returns_dict[str(item["date"])] += flt(item.get("returns", 0))
    
    # Generate all dates
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = str(current_date)
        result.append({
            "date": date_str,
            "sales": flt(sales_dict.get(date_str, 0)),
            "returns": flt(returns_dict.get(date_str, 0)),
        })
        current_date = add_days(current_date, 1)
    
    return result


def _get_monthly_sales_data(filters: Dict, warehouse_filter: Dict, company: str) -> List[Dict]:
    """Get monthly sales data from both Sales Invoice and POS Invoice."""
    SalesInvoice = DocType("Sales Invoice")
    SalesInvoiceItem = DocType("Sales Invoice Item")
    POSInvoice = DocType("POS Invoice")
    POSInvoiceItem = DocType("POS Invoice Item")
    
    # Helper to apply filters
    def apply_filters(query, Invoice):
        if filters.get("company"):
            query = query.where(Invoice.company == filters["company"])
        if filters.get("owner"):
            query = query.where(Invoice.owner == filters["owner"])
        if filters.get("posting_date"):
            if isinstance(filters["posting_date"], list) and filters["posting_date"][0] == "between":
                query = query.where(
                    Invoice.posting_date.between(
                        filters["posting_date"][1][0],
                        filters["posting_date"][1][1]
                    )
                )
        return query
    
    # Get Sales Invoice sales by month
    if warehouse_filter.get("warehouse"):
        si_sales_query = (
            frappe.qb.from_(SalesInvoice)
            .join(SalesInvoiceItem)
            .on(SalesInvoice.name == SalesInvoiceItem.parent)
            .where(SalesInvoice.docstatus == 1)
            .where(SalesInvoice.is_return == 0)
            .where(SalesInvoiceItem.warehouse == warehouse_filter["warehouse"])
        )
        si_sales_query = apply_filters(si_sales_query, SalesInvoice)
        si_sales_data = (
            si_sales_query
            .select(
                fn.DateFormat(SalesInvoice.posting_date, "%Y-%m").as_("month"),
                fn.Sum(SalesInvoiceItem.base_amount).as_("sales"),
                fn.Sum(SalesInvoiceItem.base_net_amount).as_("net")
            )
            .groupby(fn.DateFormat(SalesInvoice.posting_date, "%Y-%m"))
            .run(as_dict=True)
        )
    else:
        si_sales_query = (
            frappe.qb.from_(SalesInvoice)
            .where(SalesInvoice.docstatus == 1)
            .where(SalesInvoice.is_return == 0)
        )
        si_sales_query = apply_filters(si_sales_query, SalesInvoice)
        si_sales_data = (
            si_sales_query
            .select(
                fn.DateFormat(SalesInvoice.posting_date, "%Y-%m").as_("month"),
                fn.Sum(SalesInvoice.grand_total).as_("sales"),
                fn.Sum(SalesInvoice.base_net_total).as_("net")
            )
            .groupby(fn.DateFormat(SalesInvoice.posting_date, "%Y-%m"))
            .run(as_dict=True)
        )
    
    # Get POS Invoice sales by month
    if warehouse_filter.get("warehouse"):
        pos_sales_query = (
            frappe.qb.from_(POSInvoice)
            .join(POSInvoiceItem)
            .on(POSInvoice.name == POSInvoiceItem.parent)
            .where(POSInvoice.docstatus == 1)
            .where(POSInvoice.is_return == 0)
            .where(POSInvoiceItem.warehouse == warehouse_filter["warehouse"])
        )
        pos_sales_query = apply_filters(pos_sales_query, POSInvoice)
        pos_sales_data = (
            pos_sales_query
            .select(
                fn.DateFormat(POSInvoice.posting_date, "%Y-%m").as_("month"),
                fn.Sum(POSInvoiceItem.base_amount).as_("sales"),
                fn.Sum(POSInvoiceItem.base_net_amount).as_("net")
            )
            .groupby(fn.DateFormat(POSInvoice.posting_date, "%Y-%m"))
            .run(as_dict=True)
        )
    else:
        pos_sales_query = (
            frappe.qb.from_(POSInvoice)
            .where(POSInvoice.docstatus == 1)
            .where(POSInvoice.is_return == 0)
        )
        pos_sales_query = apply_filters(pos_sales_query, POSInvoice)
        pos_sales_data = (
            pos_sales_query
            .select(
                fn.DateFormat(POSInvoice.posting_date, "%Y-%m").as_("month"),
                fn.Sum(POSInvoice.grand_total).as_("sales"),
                fn.Sum(POSInvoice.base_net_total).as_("net")
            )
            .groupby(fn.DateFormat(POSInvoice.posting_date, "%Y-%m"))
            .run(as_dict=True)
        )
    
    # Get returns by month from both
    si_returns_query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.is_return == 1)
    )
    si_returns_query = apply_filters(si_returns_query, SalesInvoice)
    
    pos_returns_query = (
        frappe.qb.from_(POSInvoice)
        .where(POSInvoice.docstatus == 1)
        .where(POSInvoice.is_return == 1)
    )
    pos_returns_query = apply_filters(pos_returns_query, POSInvoice)
    
    si_returns_data = (
        si_returns_query
        .select(
            fn.DateFormat(SalesInvoice.posting_date, "%Y-%m").as_("month"),
            fn.Sum(fn.Abs(SalesInvoice.grand_total)).as_("returns")
        )
        .groupby(fn.DateFormat(SalesInvoice.posting_date, "%Y-%m"))
        .run(as_dict=True)
    )
    pos_returns_data = (
        pos_returns_query
        .select(
            fn.DateFormat(POSInvoice.posting_date, "%Y-%m").as_("month"),
            fn.Sum(fn.Abs(POSInvoice.grand_total)).as_("returns")
        )
        .groupby(fn.DateFormat(POSInvoice.posting_date, "%Y-%m"))
        .run(as_dict=True)
    )
    
    # Combine data from both
    sales_dict = defaultdict(lambda: {"sales": 0.0, "net": 0.0})
    returns_dict = defaultdict(float)
    
    for item in si_sales_data:
        sales_dict[item["month"]]["sales"] += flt(item.get("sales", 0))
        sales_dict[item["month"]]["net"] += flt(item.get("net", 0))
    for item in pos_sales_data:
        sales_dict[item["month"]]["sales"] += flt(item.get("sales", 0))
        sales_dict[item["month"]]["net"] += flt(item.get("net", 0))
    
    for item in si_returns_data:
        returns_dict[item["month"]] += flt(item.get("returns", 0))
    for item in pos_returns_data:
        returns_dict[item["month"]] += flt(item.get("returns", 0))
    
    # Format and return
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    result = []
    for month, data in sales_dict.items():
        month_num = int(month.split("-")[1]) - 1
        result.append({
            "month": month_names[month_num],
            "sales": flt(data["sales"]),
            "returns": flt(returns_dict.get(month, 0)),
            "net": flt(data["net"]),
        })
    
    return result


def _get_sales_due(filters: Dict, company: str) -> List[Dict]:
    """Get outstanding sales invoices."""
    SalesInvoice = DocType("Sales Invoice")
    
    query = (
        frappe.qb.from_(SalesInvoice)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.outstanding_amount > 0)
    )
    
    if filters.get("company"):
        query = query.where(SalesInvoice.company == filters["company"])
    if filters.get("owner"):
        query = query.where(SalesInvoice.owner == filters["owner"])
    
    results = (
        query
        .select(
            SalesInvoice.name,
            SalesInvoice.customer_name.as_("customer"),
            SalesInvoice.outstanding_amount.as_("amount"),
            SalesInvoice.due_date.as_("dueDate"),
            SalesInvoice.status
        )
        .orderby(SalesInvoice.due_date)
        .limit(20)
        .run(as_dict=True)
    )
    
    # Format status
    formatted_results = []
    for item in results:
        status = "Overdue" if getdate(item.get("dueDate")) < getdate() else "Due Soon"
        formatted_results.append({
            "id": item["name"],
            "customer": item["customer"],
            "amount": flt(item["amount"]),
            "dueDate": str(item["dueDate"]) if item.get("dueDate") else None,
            "status": status,
        })
    
    return formatted_results


def _get_purchases_due(filters: Dict, company: str) -> List[Dict]:
    """Get outstanding purchase invoices."""
    PurchaseInvoice = DocType("Purchase Invoice")
    
    query = (
        frappe.qb.from_(PurchaseInvoice)
        .where(PurchaseInvoice.docstatus == 1)
        .where(PurchaseInvoice.outstanding_amount > 0)
    )
    
    if filters.get("company"):
        query = query.where(PurchaseInvoice.company == filters["company"])
    if filters.get("owner"):
        query = query.where(PurchaseInvoice.owner == filters["owner"])
    
    results = (
        query
        .select(
            PurchaseInvoice.name,
            PurchaseInvoice.supplier_name.as_("supplier"),
            PurchaseInvoice.outstanding_amount.as_("amount"),
            PurchaseInvoice.due_date.as_("dueDate"),
            PurchaseInvoice.status
        )
        .orderby(PurchaseInvoice.due_date)
        .limit(20)
        .run(as_dict=True)
    )
    
    # Format status
    formatted_results = []
    for item in results:
        status = "Overdue" if getdate(item.get("dueDate")) < getdate() else "Due Soon"
        formatted_results.append({
            "id": item["name"],
            "supplier": item["supplier"],
            "amount": flt(item["amount"]),
            "dueDate": str(item["dueDate"]) if item.get("dueDate") else None,
            "status": status,
        })
    
    return formatted_results


def _get_stock_alerts(warehouse_filter: Dict, company: str) -> List[Dict]:
    """Get stock alerts for low stock items."""
    Item = DocType("Item")
    Bin = DocType("Bin")
    
    query = (
        frappe.qb.from_(Item)
        .left_join(Bin)
        .on(Item.name == Bin.item_code)
        .where(Item.is_stock_item == 1)
        .where(Item.disabled == 0)
    )
    
    if warehouse_filter.get("warehouse"):
        query = query.where(Bin.warehouse == warehouse_filter["warehouse"])
    
    # Get items with stock below minimum
    # Only show alerts for items where min_order_qty is set (not NULL) and actual_qty < min_order_qty
    results = (
        query
        .select(
            Item.name.as_("item_code"),
            Item.item_name.as_("product"),
            fn.Coalesce(Bin.actual_qty, 0).as_("currentStock"),
            fn.Coalesce(Item.min_order_qty, 0).as_("minStock")
        )
        .where(Item.min_order_qty.isnotnull())
        .where(Item.min_order_qty > 0)
        .where(fn.Coalesce(Bin.actual_qty, 0) < Item.min_order_qty)
        .limit(20)
        .run(as_dict=True)
    )
    
    formatted_results = []
    for item in results:
        current = flt(item.get("currentStock", 0))
        minimum = flt(item.get("minStock", 0))
        
        if current == 0:
            status = "Critical"
        elif current < minimum * 0.5:
            status = "Critical"
        elif current < minimum:
            status = "Low"
        else:
            status = "Warning"
        
        formatted_results.append({
            "id": item["item_code"],
            "product": item["product"],
            "currentStock": current,
            "minStock": minimum,
            "status": status,
        })
    
    return formatted_results


def _get_pending_shipments(filters: Dict, company: str) -> List[Dict]:
    """Get pending shipments/delivery notes."""
    DeliveryNote = DocType("Delivery Note")
    
    query = (
        frappe.qb.from_(DeliveryNote)
        .where(DeliveryNote.docstatus == 1)
        .where(DeliveryNote.status.isin(["To Deliver", "To Bill"]))
    )
    
    if filters.get("company"):
        query = query.where(DeliveryNote.company == filters["company"])
    if filters.get("owner"):
        query = query.where(DeliveryNote.owner == filters["owner"])
    
    results = (
        query
        .select(
            DeliveryNote.name.as_("orderId"),
            DeliveryNote.customer_name.as_("customer"),
            DeliveryNote.status,
            DeliveryNote.posting_date.as_("estDelivery")
        )
        .orderby(DeliveryNote.posting_date)
        .limit(20)
        .run(as_dict=True)
    )
    
    # Get item counts
    DeliveryNoteItem = DocType("Delivery Note Item")
    formatted_results = []
    for item in results:
        item_count = frappe.db.get_value(
            "Delivery Note Item",
            {"parent": item["orderId"]},
            ["count(name)"],
            as_dict=True
        )
        
        status_map = {
            "To Deliver": "Processing",
            "To Bill": "Processing",
            "Completed": "Shipped",
        }
        
        formatted_results.append({
            "id": item["orderId"],
            "orderId": item["orderId"],
            "customer": item["customer"],
            "items": int(item_count) if item_count else 0,
            "status": status_map.get(item["status"], "Processing"),
            "estDelivery": str(item["estDelivery"]) if item.get("estDelivery") else None,
        })
    
    return formatted_results
