import asyncio
import json

import aiohttp
import frappe
import frappe.defaults
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import cint

from ..background_tasks.task_response_handlers import (
    operation_types_search_on_success,
    uom_category_search_on_success,
    uom_search_on_success,
)
from ..doctype.doctype_names_mapping import (
    COUNTRIES_DOCTYPE_NAME,
    OPERATION_TYPE_DOCTYPE_NAME,
    REGISTERED_PURCHASES_DOCTYPE_NAME,
    SETTINGS_DOCTYPE_NAME,
    SLADE_ID_MAPPING_DOCTYPE_NAME,
    UOM_CATEGORY_DOCTYPE_NAME,
    USER_DOCTYPE_NAME,
)
from ..utils import (
    build_return_invoice_payload,
    generate_custom_item_code_etims,
    get_active_settings,
    get_invoice_reference_number,
    get_link_value,
    get_settings,
    get_slade360_id,
    make_get_request,
)
from .api_builder import EndpointsBuilder
from .process_request import process_request
from .account_provisioning_api import validate_and_get_provisional_account
from .remote_response_status_handlers import (
    customer_branch_details_submission_on_success,
    customer_search_on_success,
    customers_search_on_success,
    fetch_matching_items_on_success,
    fetch_matching_partner_on_success,
    imported_item_submission_on_success,
    imported_items_search_on_success,
    initialize_device_submission_on_success,
    item_composition_submission_on_success,
    item_price_update_on_success,
    item_search_on_success,
    mode_of_payment_on_success,
    pricelist_update_on_success,
    purchase_search_on_success,
    sales_information_submission_on_success,
    submit_inventory_on_success,
    update_invoice_info,
    user_details_fetch_on_success,
    user_details_submission_on_success,
    verify_and_fix_invoice_info,
)

endpoints_builder = EndpointsBuilder()

@frappe.whitelist()
def bulk_submit_sales_invoices(docs_list: str = None, settings_name: str = None) -> None:
    from ..overrides.server.sales_invoice import on_submit

    invoices_to_process = []
    
    if docs_list:
        data = json.loads(docs_list)
        all_sales_invoices = frappe.db.get_all(
            "Sales Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
        )
        
        for record in data:
            for invoice in all_sales_invoices:
                if record == invoice.name:
                    invoices_to_process.append(record)
    else:
        all_invoices = frappe.db.get_all(
            "Sales Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
        )
        invoices_to_process = [invoice.name for invoice in all_invoices]
    
    for invoice_name in invoices_to_process:
        doc = frappe.get_doc("Sales Invoice", invoice_name, for_update=False)
        frappe.enqueue(on_submit, doc=doc)

@frappe.whitelist()
def bulk_pos_sales_invoices(docs_list: str = None, settings_name: str = None) -> None:
    from ..overrides.server.pos_invoice import on_submit

    invoices_to_process = []
    
    if docs_list:
        data = json.loads(docs_list)
        all_pos_invoices = frappe.db.get_all(
            "POS Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
        )
        
        for record in data:
            for invoice in all_pos_invoices:
                if record == invoice.name:
                    invoices_to_process.append(record)
    else:
        all_invoices = frappe.db.get_all(
            "POS Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
        )
        invoices_to_process = [invoice.name for invoice in all_invoices]
    
    for invoice_name in invoices_to_process:
        doc = frappe.get_doc("POS Invoice", invoice_name, for_update=False)
        frappe.enqueue(on_submit, doc=doc, method=None)
                
@frappe.whitelist()
def bulk_verify_and_resend_invoices(docs_list: str, settings_name: str = None) -> None:
    invoices_to_process = []
    
    if docs_list:
        data = json.loads(docs_list)
        all_sales_invoices = frappe.db.get_all(
            "Sales Invoice", {"docstatus": 1}, ["name"]
        )
        
        for record in data:
            for invoice in all_sales_invoices:
                if record == invoice.name:
                    invoices_to_process.append(record)
    else:
        all_invoices = frappe.db.get_all(
            "Sales Invoice", {"docstatus": 1}, ["name"]
        )
        invoices_to_process = [invoice.name for invoice in all_invoices]
    
    for invoice_name in invoices_to_process:
        doc = frappe.get_doc("Sales Invoice", invoice_name, for_update=False)
        frappe.enqueue(
            get_invoice_details, 
            id=None,
            document_name=doc.name, 
            invoice_type="Sales Invoice",
            settings_name=settings_name,
            company=doc.company
        )

@frappe.whitelist()
def bulk_register_items(docs_list: str, settings_name: str = None) -> None:
    item_names = json.loads(docs_list)
    settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    
    if not item_names or not settings:
        return
    
    for setting in settings:
        for item_name in item_names:
            frappe.enqueue(
                perform_item_registration,
                item_name=item_name,
                settings_name=setting.name
            )


@frappe.whitelist()
def update_all_items(settings_name: str = None) -> None:
    settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    
    if not settings:
        return
    
    for setting in settings:
        Item = DocType("Item")
        Mapping = DocType(SLADE_ID_MAPPING_DOCTYPE_NAME)
        
        items = (
            frappe.qb.from_(Item)
            .inner_join(Mapping)
            .on(
                (Mapping.parent == Item.name) &
                (Mapping.parenttype == "Item") &
                (Mapping.etims_setup == setting.name)
            )
            .select(Item.name)
            .where(Item.custom_sent_to_slade == 1)
            .run(as_dict=True)
        )
        
        for item in items:
            frappe.enqueue(
                perform_item_registration,
                item_name=item.name,
                settings_name=setting.name,
            )

@frappe.whitelist()
def register_all_items(settings_name: str = None) -> None:
    settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()

    if not settings:
        return

    for setting in settings:
        Item = DocType("Item")
        Mapping = DocType(SLADE_ID_MAPPING_DOCTYPE_NAME)
        
        items = (
            frappe.qb.from_(Item)
            .left_join(Mapping)
            .on(
                (Mapping.parent == Item.name) &
                (Mapping.parenttype == "Item") &
                (Mapping.etims_setup == setting.name)
            )
            .select(Item.name)
            .where(
                (Item.custom_sent_to_slade == 0) &
                (Mapping.name.isnull())
            )
            .run(as_dict=True)
        )
        
        for item in items:
            frappe.enqueue(
                perform_item_registration,
                item_name=item.name,
                settings_name=setting.name
            )


@frappe.whitelist()
def perform_customer_search(request_data: str) -> None:
    """Search customer details in the eTims Server

    Args:
        request_data (str): Data received from the client
    """
    return process_request(
        request_data,
        "CustSearchReq",
        customer_search_on_success,
        request_method="POST",
        doctype="Customer",
    )


@frappe.whitelist()
def perform_item_registration(item_name: str, settings_name: str) -> dict | None:
    """Main function to handle item registration with SLADE"""
    item = frappe.get_doc("Item", item_name)

    if not is_item_eligible_for_registration(item):
        return None

    missing_fields = validate_required_fields(item)
    if missing_fields:
        return None

    if not item.custom_item_code_etims:
        generate_and_set_etims_code(item)
    
    frappe.enqueue(
        process_request,
        queue="default",
        is_async=True,
        request_data={"name": item.name, "document_name": item.name},
        route_key="ItemsSearchReq",
        handler_function=fetch_matching_items_on_success,
        request_method="GET",
        doctype="Item",
        settings_name=settings_name,
    )
    
    

def is_item_eligible_for_registration(item) -> bool:
    """Check if item meets basic registration criteria"""
    return not (item.custom_prevent_etims_registration or item.disabled)

def validate_required_fields(item) -> list:
    """Validate required fields for item registration"""
    required_fields = [
        "custom_item_classification",
        "custom_product_type",
        "custom_item_type",
        "custom_etims_country_of_origin_code",
        "custom_packaging_unit",
        "custom_unit_of_quantity",
        "custom_taxation_type",
    ]
    return [field for field in required_fields if not item.get(field)]

def generate_and_set_etims_code(item) -> None:
    """Generate and set ETIMS code for item"""
    item.custom_item_code_etims = generate_custom_item_code_etims(item)
    frappe.db.set_value(
        "Item", item.name, "custom_item_code_etims", item.custom_item_code_etims
    )
    frappe.db.commit()


@frappe.whitelist()
def fetch_item_details(request_data: str, settings_name: str) -> None:
    process_request(
        request_data, "ItemSearchReq", item_search_on_success, doctype="Item", settings_name=settings_name
    )


@frappe.whitelist()
def submit_all_suppliers(settings_name: str = None) -> None:
    active_settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    if not active_settings:
        return
    for setting in active_settings:
        
        Supplier = DocType("Supplier")
        Mapping = DocType(SLADE_ID_MAPPING_DOCTYPE_NAME)
        
        query = (
            frappe.qb.from_(Supplier)
            .left_join(Mapping)
            .on(
                (Mapping.parent == Supplier.name) & 
                (Mapping.parenttype == "Supplier") & 
                (Mapping.etims_setup == setting.name)
            )
            .select(Supplier.name)
            .where(
                (Mapping.name.isnull())
            )
        )
        
        suppliers = query.run(as_dict=True)
                
        for supplier in suppliers:
            frappe.enqueue(
                send_branch_customer_details, 
                settings_name=setting.name, 
                name=supplier.name, 
                is_customer=False
            )

            
            
@frappe.whitelist()
def bulk_submit_suppliers(docs_list: str, settings_name: str = None) -> None:
    suppliers = json.loads(docs_list)
    settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    if not suppliers or not settings:
        return
    
    for setting in settings:
        for supplier in suppliers:
            frappe.enqueue(
                send_branch_customer_details,
                name=supplier, 
                is_customer=False,
                settings_name=setting.name
            )
            
            
@frappe.whitelist()
def bulk_submit_customers(docs_list: str, settings_name: str = None) -> None:
    customers = json.loads(docs_list)
    settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    if not customers or not settings:
        return
    
    for setting in settings:
        for customer in customers:
            frappe.enqueue(
                send_branch_customer_details,
                name=customer, 
                is_customer=True,
                settings_name=setting.name
            )

@frappe.whitelist()
def submit_all_customers(settings_name: str = None) -> None:
    active_settings = [frappe.get_doc(SETTINGS_DOCTYPE_NAME, settings_name)] if settings_name else get_active_settings()
    if not active_settings:
        return
    for setting in active_settings:
        
        Customer = DocType("Customer")
        Mapping = DocType(SLADE_ID_MAPPING_DOCTYPE_NAME)
        
        query = (
            frappe.qb.from_(Customer)
            .left_join(Mapping)
            .on(
                (Mapping.parent == Customer.name) & 
                (Mapping.parenttype == "Customer") & 
                (Mapping.etims_setup == setting.name)
            )
            .select(Customer.name)
            .where( 
                (Mapping.name.isnull())
            )
        )
        
        customers = query.run(as_dict=True)
        
        for customer in customers:
            frappe.enqueue(
                send_branch_customer_details, 
                settings_name=setting.name, 
                name=customer.name
            )


@frappe.whitelist()
def send_branch_customer_details(name: str, settings_name: str, is_customer: bool = True) -> None:
    doctype = "Customer" if is_customer else "Supplier"
    data = frappe.get_doc(doctype, name)

    if (hasattr(data, 'disabled') and data.disabled) or (hasattr(data, 'custom_prevent_etims_registration') and data.custom_prevent_etims_registration):
        return
    
    request_data = (
        {"customer_tax_pin": data.tax_id, "document_name": name} 
        if hasattr(data, 'tax_id') and data.tax_id is not None 
        else {"partner_name": name, "document_name": name}
    )

    frappe.enqueue(
        process_request,
        queue="default",
        is_async=True,
        request_data=request_data,
        route_key="BhfCustSaveReq",
        handler_function=fetch_matching_partner_on_success,
        request_method="GET",
        doctype=doctype,
        settings_name=settings_name,
    )
    

@frappe.whitelist()
def search_customers_request(request_data: str, settings_name: str,) -> None:
    return process_request(
        request_data, "CustomersSearchReq", customers_search_on_success, settings_name=settings_name
    )


@frappe.whitelist()
def get_customer_details(request_data: str, settings_name: str,) -> None:
    return process_request(
        request_data, "CustomerSearchReq", customers_search_on_success, settings_name=settings_name
    )


@frappe.whitelist()
def get_my_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSearchReq",
        user_details_fetch_on_success,
        request_method="GET",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def get_branch_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSaveReq",
        user_details_fetch_on_success,
        request_method="GET",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def save_branch_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSaveReq",
        user_details_submission_on_success,
        request_method="POST",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def create_branch_user() -> None:
    # TODO: Implement auto-creation through background tasks
    present_users = frappe.db.get_all(
        "User", {"name": ["not in", ["Administrator", "Guest"]]}, ["name", "email"]
    )

    for user in present_users:
        if not frappe.db.exists(USER_DOCTYPE_NAME, {"email": user.email}):
            doc = frappe.new_doc(USER_DOCTYPE_NAME)

            doc.system_user = user.email
            doc.branch_id = frappe.get_value(
                "Branch",
                {"custom_branch_code": frappe.get_value("Branch", "name")},
                ["name"],
            )  # Created users are assigned to Branch 00

            doc.save(ignore_permissions=True)

    frappe.msgprint("Inspect the Branches to make sure they are mapped correctly")


@frappe.whitelist()
def perform_item_search(request_data: str, settings_name: str) -> None:

    process_request(
        request_data, "ItemsSearchReq", item_search_on_success, doctype="Item", settings_name=settings_name
    )


@frappe.whitelist()
def perform_import_item_search(request_data: str, settings_name: str) -> None:
    process_request(
        request_data,
        "ImportItemSearchReq",
        imported_items_search_on_success,
        doctype="Item",
        settings_name=settings_name,
    )


@frappe.whitelist()
def perform_import_item_search_all_branches() -> None:
    all_credentials = frappe.get_all(
        SETTINGS_DOCTYPE_NAME,
        ["name", "bhfid", "company"],
    )

    for credential in all_credentials:
        request_data = json.dumps(
            {"company_name": credential.company, "branch_code": credential.bhfid}
        )

        perform_import_item_search(request_data, settings_name=credential.name)


@frappe.whitelist()
def perform_purchases_search(request_data: str) -> None:
    process_request(
        request_data,
        "TrnsPurchaseSalesReq",
        purchase_search_on_success,
        doctype=REGISTERED_PURCHASES_DOCTYPE_NAME,
    )


@frappe.whitelist()
def perform_purchase_search(request_data: str) -> None:
    process_request(
        request_data,
        "TrnsPurchaseSearchReq",
        purchase_search_on_success,
        doctype=REGISTERED_PURCHASES_DOCTYPE_NAME,
    )

@frappe.whitelist()
def send_entire_stock_balance(settings_name: str) -> None:
    Item = frappe.qb.DocType("Item")
    Mapping = frappe.qb.DocType(SLADE_ID_MAPPING_DOCTYPE_NAME)
    
    query = (
        frappe.qb.from_(Item)
        .inner_join(Mapping)
        .on(
            (Mapping.parent == Item.name) &
            (Mapping.parenttype == "Item") &
            (Mapping.etims_setup == settings_name)
        )
        .select(Item.name, Item.item_code, Item.item_name)
        .where(
            (Item.is_stock_item == 1) &
            (Item.custom_sent_to_slade == 1)
        )
    )
    
    items = query.run(as_dict=True)
    
    for item in items:
        frappe.enqueue(
            submit_inventory,
            name=item.name,
            settings_name=settings_name
        )


@frappe.whitelist()
def submit_inventory(name: str, settings_name: str) -> None:
    # TODO: Redesign this function to work with the new structure for Stock Submission
    # pass
    if not name:
        frappe.throw("Item name is required.")

    settings = get_settings(settings_name=settings_name)
    
    if not settings:
        return

    request_data = {
        "document_name": name,
        "inventory_reference": name,
        "description": f"{name} Stock Adjustment for {name}",
        "reason": "Opening Stock",
        "source_organisation_unit": get_link_value(
            "Department",
            "name",
            settings.organisation_mapping[0].department,
            "custom_slade_id",
        ),
        "location": get_link_value(
            "Warehouse",
            "name",
            settings.organisation_mapping[0].get("warehouse"),
            "custom_slade_id",
        ),
    }
    process_request(
        request_data,
        route_key="StockMasterSaveReq",
        handler_function=submit_inventory_on_success,
        request_method="POST",
        doctype="Item",
        settings_name=settings_name,
    )


@frappe.whitelist()
def update_stock_quantity(name: str, id: str) -> None:
    if not name:
        frappe.throw("Item name is required.")

    stock_levels = frappe.db.get_all(
        "Bin",
        filters={"item_code": name},
        fields=["actual_qty"],
    )

    if not stock_levels:
        frappe.log_error(
            f"No stock levels found for item {name}.", "Stock Update Error"
        )
    else:
        request_data = {
            "id": id,
            "document_name": name,
            "quantity": sum(
                [float(stock.get("actual_qty", 0)) for stock in stock_levels]
            ),
        }
        process_request(
            request_data,
            route_key="SaveStockBalanceReq",
            # handler_function=submit_inventory_on_success,
            request_method="PATCH",
            doctype="Item",
        )


@frappe.whitelist()
def send_imported_item_request(request_data: str) -> None:
    process_request(
        request_data,
        "ImportItemSearchReq",
        imported_item_submission_on_success,
        request_method="POST",
        doctype="Item",
    )


@frappe.whitelist()
def update_imported_item_request(request_data: str) -> None:
    process_request(
        request_data,
        "ImportItemUpdateReq",
        imported_item_submission_on_success,
        method="PUT",
        doctype="Item",
    )


@frappe.whitelist()
def submit_item_composition(name: str) -> None:
    item = frappe.get_doc("BOM", name)
    request_data = {
        "final_product": get_link_value("Item", "name", item.item, "custom_slade_id"),
        "document_name": name,
    }
    process_request(
        request_data,
        "BOMReq",
        item_composition_submission_on_success,
        request_method="POST",
        doctype="BOM",
    )


@frappe.whitelist()
def create_supplier_from_fetched_registered_purchases(request_data: str) -> None:
    data: dict = json.loads(request_data)

    new_supplier = create_supplier(data)

    frappe.msgprint(f"Supplier: {new_supplier.name} created")


def create_supplier(supplier_details: dict) -> Document:
    new_supplier = frappe.new_doc("Supplier")

    new_supplier.supplier_name = supplier_details["supplier_name"]
    new_supplier.tax_id = supplier_details["supplier_pin"]
    new_supplier.custom_supplier_branch = supplier_details["supplier_branch_id"]

    if "supplier_currency" in supplier_details:
        new_supplier.default_currency = supplier_details["supplier_currency"]

    if "supplier_nation" in supplier_details:
        new_supplier.country = supplier_details["supplier_nation"].capitalize()

    new_supplier.insert(ignore_if_duplicate=True)

    return new_supplier


@frappe.whitelist()
def create_items_from_fetched_registered(request_data: str) -> None:
    data = json.loads(request_data)

    if data["items"]:
        items = data["items"]
        for item in items:
            create_item(item)


def create_item(item: dict | frappe._dict) -> Document:
    item_code = item.get("item_code", None)

    new_item = frappe.new_doc("Item")
    new_item.is_stock_item = 0  # Default to 0
    new_item.item_code = item["product_code"]
    new_item.item_name = item["item_name"]
    new_item.item_group = "All Item Groups"
    if "item_classification_code" in item:
        new_item.custom_item_classification = item["item_classification_code"]
    new_item.custom_packaging_unit = item["packaging_unit_code"]
    new_item.custom_unit_of_quantity = (
        item.get("quantity_unit_code", None) or item["unit_of_quantity_code"]
    )
    new_item.custom_taxation_type = item["taxation_type_code"]
    new_item.custom_etims_country_of_origin = (
        frappe.get_doc(
            COUNTRIES_DOCTYPE_NAME,
            {"code": item_code[:2]},
            for_update=False,
        ).name
        if item_code
        else None
    )
    new_item.custom_product_type = item_code[2:3] if item_code else None

    if item_code and int(item_code[2:3]) != 3:
        new_item.is_stock_item = 1
    else:
        new_item.is_stock_item = 0

    new_item.custom_item_code_etims = item["item_code"]
    new_item.valuation_rate = item["unit_price"]

    if "imported_item" in item:
        new_item.is_stock_item = 1
        new_item.custom_referenced_imported_item = item["imported_item"]

    new_item.insert(ignore_mandatory=True, ignore_if_duplicate=True)

    return new_item


@frappe.whitelist()
def create_purchase_invoice_from_request(request_data: str) -> None:
    data = json.loads(request_data)

    if not data.get("company_name"):
        data["company_name"] = frappe.defaults.get_user_default(
            "Company"
        ) or frappe.get_value("Company", {}, "name")

    # Check if supplier exists
    supplier = None
    if not frappe.db.exists("Supplier", data["supplier_name"], cache=False):
        supplier = create_supplier(data).name

    all_items = []
    all_existing_items = {
        item["name"]: item for item in frappe.db.get_all("Item", ["*"])
    }

    for received_item in data["items"]:
        # Check if item exists
        if received_item["item_name"] not in all_existing_items:
            created_item = create_item(received_item)
            all_items.append(created_item)

    set_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": data["branch"]},
        ["name"],
        as_dict=True,
    )

    if not set_warehouse:
        set_warehouse = frappe.get_value(
            "Warehouse", {"is_group": 0, "company": data["company_name"]}, "name"
        )  # use first warehouse match if not available for the branch

    # Create the Purchase Invoice
    purchase_invoice = frappe.new_doc("Purchase Invoice")
    purchase_invoice.supplier = supplier or data["supplier_name"]
    purchase_invoice.supplier = supplier or data["supplier_name"]
    purchase_invoice.update_stock = 1
    purchase_invoice.set_warehouse = set_warehouse
    purchase_invoice.branch = data["branch"]
    purchase_invoice.company = data["company_name"]
    purchase_invoice.custom_slade_organisation = data["organisation"]
    purchase_invoice.bill_no = data["supplier_invoice_no"]
    purchase_invoice.bill_date = data["supplier_invoice_date"]
    purchase_invoice.bill_date = data["supplier_invoice_date"]

    if "currency" in data:
        # The "currency" key is only available when creating from Imported Item
        purchase_invoice.currency = data["currency"]
        purchase_invoice.custom_source_registered_imported_item = data["name"]
    else:
        purchase_invoice.custom_source_registered_purchase = data["name"]

    if "exchange_rate" in data:
        purchase_invoice.conversion_rate = data["exchange_rate"]

    purchase_invoice.set("items", [])

    # TODO: Remove Hard-coded values
    purchase_invoice.custom_purchase_type = "Copy"
    purchase_invoice.custom_receipt_type = "Purchase"
    purchase_invoice.custom_payment_type = "CASH"
    purchase_invoice.custom_purchase_status = "Approved"

    company_abbr = frappe.get_value(
        "Company", {"name": frappe.defaults.get_user_default("Company")}, ["abbr"]
    )
    expense_account = frappe.db.get_value(
        "Account",
        {
            "name": [
                "like",
                f"%Cost of Goods Sold%{company_abbr}",
            ]
        },
        ["name"],
    )

    for item in data["items"]:
        matching_item = frappe.get_all(
            "Item",
            filters={
                "item_name": item["item_name"],
                "custom_item_classification": item["item_classification_code"],
            },
            fields=["name"],
        )
        item_code = matching_item[0]["name"]
        purchase_invoice.append(
            "items",
            {
                "item_name": item["item_name"],
                "item_code": item_code,
                "qty": item["quantity"],
                "rate": item["unit_price"],
                "expense_account": expense_account,
                "custom_item_classification": item["item_classification_code"],
                "custom_packaging_unit": item["packaging_unit_code"],
                "custom_unit_of_quantity": item["quantity_unit_code"],
                "custom_taxation_type": item["taxation_type_code"],
            },
        )

    purchase_invoice.insert(ignore_mandatory=True)

    frappe.msgprint("Purchase Invoices have been created")


@frappe.whitelist()
def ping_server(request_data: str) -> None:
    data = json.loads(request_data)
    server_url = data.get("server_url")
    auth_url = data.get("auth_url")

    async def check_server(url: str) -> tuple:
        try:
            response = await make_get_request(url)
            return "Online", response
        except aiohttp.client_exceptions.ClientConnectorError:
            return "Offline", None

    async def main() -> None:
        server_status, server_response = await check_server(server_url)
        auth_status, auth_response = await check_server(auth_url)

        if server_response:
            frappe.msgprint(f"Server Status: {server_status}\n{server_response}")
        else:
            frappe.msgprint(f"Server Status: {server_status}")

        frappe.msgprint(f"Auth Server Status: {auth_status}")

    asyncio.run(main())


@frappe.whitelist()
def create_stock_entry_from_stock_movement(request_data: str) -> None:
    data = json.loads(request_data)

    for item in data["items"]:
        if not frappe.db.exists("Item", item["item_name"], cache=False):
            # Create item if item doesn't exist
            create_item(item)

    # Create stock entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"

    stock_entry.set("items", [])

    source_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": data["branch_id"]},
        ["name"],
        as_dict=True,
    )

    target_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": "01"},  # TODO: Fix hardcode from 01 to a general solution
        ["name"],
        as_dict=True,
    )

    for item in data["items"]:
        stock_entry.append(
            "items",
            {
                "s_warehouse": source_warehouse.name,
                "t_warehouse": target_warehouse.name,
                "item_code": item["item_name"],
                "qty": item["quantity"],
            },
        )

    stock_entry.save(ignore_permissions=True)

    frappe.msgprint(f"Stock Entry {stock_entry.name} created successfully")


@frappe.whitelist()
def initialize_device(request_data: str) -> None:
    return process_request(
        request_data,
        "DeviceVerificationReq",
        initialize_device_submission_on_success,
        request_method="POST",
        doctype=SETTINGS_DOCTYPE_NAME,
    )
    
    
@frappe.whitelist()
def _process_invoice_fetch_request(
    id: str = None, 
    document_name: str = None, 
    invoice_type: str = "Sales Invoice", 
    settings_name: str = None, 
    company: str = None,
    handler_function = None,
    reference_number: str = None, 
    is_return: bool = False,
    original_invoice_id: str = None,
) -> None:
    """Common helper function to process invoice-related requests."""
    invoice = frappe.get_doc(invoice_type, document_name)
    
    if is_return and not original_invoice_id:
        frappe.throw("Original invoice ID is required for return processing.")

    request_data = {
        "document_name": document_name,
        "company": company or invoice.company,
    }
    
    route_key = "TrnsSalesSearchReq"
    
    if invoice.is_return or is_return:
        route_key = "SalesCreditNoteSaveReq"
    
    if id:
        request_data["id"] = id
    else:
        if (invoice.is_return and invoice.return_against) or (is_return and original_invoice_id):
            route_key = "SalesCreditNoteSaveReq"
            original_invoice_slade_id = original_invoice_id if is_return else frappe.db.get_value("Sales Invoice", invoice.return_against, "custom_slade_id")
            request_data["invoice"] = original_invoice_slade_id
        else:
            route_key = "TrnsSalesSaveWrReq"
            request_data["reference_number"] = reference_number
    
    return process_request(
        request_data,
        route_key,
        handler_function,
        doctype=invoice_type,
        settings_name=settings_name,
        company=company,
    )


@frappe.whitelist()
def get_invoice_details(
    id: str = None, document_name: str = None, invoice_type: str = "Sales Invoice", settings_name: str = None, company: str = None
) -> None:
    invoice = frappe.get_doc(invoice_type, document_name)
    reference_number = get_invoice_reference_number(invoice)
    _process_invoice_fetch_request(
        id=id,
        document_name=document_name,
        invoice_type=invoice_type,
        settings_name=settings_name,
        company=company,
        handler_function=update_invoice_info,
        reference_number=reference_number,
    )


@frappe.whitelist()
def verify_invoice_details(
    id: str = None, document_name: str = None, invoice_type: str = "Sales Invoice", settings_name: str = None, company: str = None
) -> None:
    invoice = frappe.get_doc(invoice_type, document_name)
    reference_number = get_invoice_reference_number(invoice)
    _process_invoice_fetch_request(
        id=id,
        document_name=document_name,
        invoice_type=invoice_type,
        settings_name=settings_name,
        company=company,
        handler_function=verify_and_fix_invoice_info,
        reference_number=reference_number,
    )



@frappe.whitelist()
def save_uom_category_details(name: str) -> dict | None:
    item = frappe.get_doc(UOM_CATEGORY_DOCTYPE_NAME, name)

    slade_id = item.get("slade_id", None)

    request_data = {
        "name": item.get("category_name"),
        "document_name": item.get("name"),
        "measure_type": item.get("measure_type"),
        "active": True if item.get("active") == 1 else False,
    }

    if slade_id:
        request_data["id"] = slade_id
        process_request(
            request_data,
            "UOMCategoriesSearchReq",
            uom_category_search_on_success,
            request_method="PATCH",
            doctype=UOM_CATEGORY_DOCTYPE_NAME,
        )
    else:
        process_request(
            request_data,
            "UOMCategoriesSearchReq",
            uom_category_search_on_success,
            request_method="POST",
            doctype=UOM_CATEGORY_DOCTYPE_NAME,
        )


@frappe.whitelist()
def sync_uom_category_details(request_data: str) -> None:
    process_request(
        request_data,
        "UOMCategorySearchReq",
        uom_category_search_on_success,
        doctype=UOM_CATEGORY_DOCTYPE_NAME,
    )


@frappe.whitelist()
def save_uom_details(name: str) -> dict | None:
    item = frappe.get_doc("UOM", name)

    slade_id = item.get("slade_id", None)

    request_data = {
        "name": item.get("uom_name"),
        "document_name": item.get("name"),
        "factor": item.get("custom_factor"),
        "uom_type": item.get("custom_uom_type"),
        "category": get_link_value(
            UOM_CATEGORY_DOCTYPE_NAME,
            "name",
            item.get("custom_category"),
            "slade_id",
        ),
        "active": True if item.get("active") == 1 else False,
    }

    if slade_id:
        request_data["id"] = slade_id
        process_request(
            request_data,
            "UOMListSearchReq",
            uom_search_on_success,
            request_method="PATCH",
            doctype="UOM",
        )
    else:
        process_request(
            request_data,
            "UOMListSearchReq",
            uom_search_on_success,
            request_method="POST",
            doctype="UOM",
        )


@frappe.whitelist()
def sync_uom_details(request_data: str) -> None:
    process_request(
        request_data,
        "UOMDetailSearchReq",
        uom_search_on_success,
        doctype="UOM",
    )


@frappe.whitelist()
def submit_uom_list() -> dict | None:
    uoms = frappe.get_all(
        "UOM", filters={"custom_slade_id": ["is", "not set"]}, fields=["name"]
    )
    request_data = []
    for uom in uoms:
        item = frappe.get_doc("UOM", uom.name)
        category = item.get("custom_category") or "Unit"
        item_data = {
            "name": item.get("uom_name"),
            "factor": item.get("custom_factor"),
            "uom_type": item.get("custom_uom_type") or "reference",
            "category": get_link_value(
                UOM_CATEGORY_DOCTYPE_NAME,
                "name",
                category,
                "slade_id",
            ),
            "active": True if item.get("active") == 1 else False,
        }
        request_data.append(item_data)

    process_request(
        request_data,
        "UOMListSearchReq",
        uom_search_on_success,
        request_method="POST",
        doctype="UOM",
    )


@frappe.whitelist()
def submit_pricelist(name: str) -> dict | None:
    item = frappe.get_doc("Price List", name)
    slade_id = item.get("custom_slade_id", None)

    route_key = "PriceListsSearchReq"
    on_success = pricelist_update_on_success

    # pricelist_type is mandatory for the request and cannot accept both selling and buying
    pricelist_type = (
        "selling"
        if item.get("selling") == 1
        else "purchases" if item.get("buying") == 1 else "selling"
    )
    request_data = {
        "name": item.get("price_list_name"),
        "document_name": item.get("name"),
        "pricelist_status": item.get("custom_pricelist_status"),
        "pricelist_type": pricelist_type,
        "organisation": get_link_value(
            "Company",
            "name",
            item.get("custom_company"),
            "custom_slade_id",
        ),
        "active": False if item.get("enabled") == 0 else True,
    }

    if item.get("custom_warehouse"):
        request_data["location"] = get_link_value(
            "Warehouse",
            "name",
            item.get("custom_warehouse"),
            "custom_slade_id",
        )

    if item.get("custom_effective_from"):
        request_data["effective_from"] = item.get("custom_effective_from").strftime(
            "%Y-%m-%d"
        )

    if item.get("custom_effective_to"):
        request_data["effective_to"] = item.get("custom_effective_to").strftime(
            "%Y-%m-%d"
        )

    if slade_id:
        request_data["id"] = slade_id
        method = "PATCH"
    else:
        method = "POST"

    process_request(
        request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method=method,
        doctype="Price List",
    )


@frappe.whitelist()
def sync_pricelist(request_data: str) -> None:
    process_request(
        request_data,
        "PriceListSearchReq",
        pricelist_update_on_success,
        doctype="Price List",
    )


@frappe.whitelist()
def submit_item_price(name: str) -> dict | None:
    item = frappe.get_doc("Item Price", name)
    slade_id = item.get("custom_slade_id", None)
    item_code = item.get("item_code", None)
    item_name = item.get("name", None)

    route_key = "ItemPricesSearchReq"
    on_success = item_price_update_on_success

    request_data = {
        "name": f"{item_code} - {item_name}",
        "document_name": item_name,
        "price_inclusive_tax": item.get("price_list_rate"),
        "organisation": get_link_value(
            "Company",
            "name",
            item.get("custom_company"),
            "custom_slade_id",
        ),
        "product": get_link_value(
            "Item",
            "name",
            item_code,
            "custom_slade_id",
        ),
        "currency": get_link_value(
            "Currency",
            "name",
            item.get("currency"),
            "custom_slade_id",
        ),
        "pricelist": get_link_value(
            "Price List",
            "name",
            item.get("price_list"),
            "custom_slade_id",
        ),
        "active": False if item.get("enabled") == 0 else True,
    }

    if slade_id:
        request_data["id"] = slade_id
        method = "PATCH"
    else:
        method = "POST"

    process_request(
        request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method=method,
        doctype="Item Price",
    )


@frappe.whitelist()
def sync_item_price(request_data: str) -> None:
    process_request(
        request_data,
        "ItemPriceSearchReq",
        item_price_update_on_success,
        doctype="Item Price",
    )


@frappe.whitelist()
def save_operation_type(name: str) -> dict | None:
    item = frappe.get_doc(OPERATION_TYPE_DOCTYPE_NAME, name)
    slade_id = item.get("slade_id", None)

    route_key = "OperationTypesReq"
    if item.get("destination_location") and item.get("source_location"):
        request_data = {
            "operation_name": item.get("operation_name"),
            "document_name": item.get("name"),
            "operation_type": item.get("operation_type"),
            "organisation": get_link_value(
                "Company",
                "name",
                item.get("company"),
                "custom_slade_id",
            ),
            "destination_location": item.get("destination_location"),
            "source_location": item.get("source_location"),
            "active": False if item.get("active") == 0 else True,
        }

        if slade_id:
            request_data["id"] = slade_id
            method = "PATCH"
        else:
            method = "POST"

        process_request(
            request_data,
            route_key=route_key,
            handler_function=operation_types_search_on_success,
            request_method=method,
            doctype=OPERATION_TYPE_DOCTYPE_NAME,
        )
    return None


@frappe.whitelist()
def sync_operation_type(request_data: str) -> None:
    process_request(
        request_data,
        "OperationTypeReq",
        operation_types_search_on_success,
        doctype=OPERATION_TYPE_DOCTYPE_NAME,
    )


@frappe.whitelist()
def send_all_mode_of_payments(settings_name: str) -> None:
    mode_of_payments = frappe.get_all("Mode of Payment", fields=["name"])
    
    for mop in mode_of_payments:
        send_mode_of_payment_details(mop.name, settings_name)
            


@frappe.whitelist()
def send_mode_of_payment_details(name: str, settings_name: str) -> dict | None:
    route_key = "AccountsSearchReq"
    on_success = reaceavable_accouct_search_on_success
    request_data = {
        "number": "1000-0001",
        "document_name": name,
    }
    
    frappe.enqueue(
        process_request,
        queue="default",
        is_async=True,
        doctype="Mode of Payment",
        request_data=request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method="GET",
        settings_name=settings_name,
    )


def reaceavable_accouct_search_on_success(
    response: dict, document_name: str, settings_name: str, **kwargs
) -> None:
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {response}")

    account = (
        response if isinstance(response, list) else response.get("results", [response])
    )[0]

    mode_of_payment = frappe.get_doc("Mode of Payment", document_name)

    request_data = {
        "account": account.get("id"),
        "name": mode_of_payment.get("mode_of_payment"),
        "organisation": account.get("organisation"),
        "document_name": document_name,
    }

    process_request(
        request_data,
        route_key="PaymentMtdSearchReq",
        handler_function=mode_of_payment_on_success,
        request_method="POST",
        doctype="Mode of Payment",
        settings_name=settings_name,
    )
    

@frappe.whitelist()
def submit_credit_note(response: dict, document_name: str, doctype: str, settings_name: str, **kwargs) -> None:
    doc = frappe.get_doc(doctype, document_name)
    data = response.get("results", [])[0] if response.get("results") else response
    scu_data = data.get("scu_data")
    if not scu_data:
        return
    payload = build_return_invoice_payload(doc, data)
    frappe.enqueue(
        process_request,
        queue="default",
        is_async=True,
        request_data=payload,
        route_key="CreditNoteSaveReq",
        handler_function=sales_information_submission_on_success,
        request_method="POST",
        doctype=doctype,
        settings_name=settings_name,
        company=doc.company,
    )


# ============================================================================
# PURCHASE MANAGEMENT ENDPOINTS
# ============================================================================

@frappe.whitelist()
def create_purchase_invoice(
    supplier: str,
    company: str,
    items: list,
    posting_date: str = None,
    bill_no: str = None,
    bill_date: str = None,
    branch: str = None,
    warehouse: str = None,
    currency: str = None,
    taxes: list = None,
    update_stock: bool = False,
    prevent_etims_submission: bool = False,
    settings_name: str = None,
    # Payment fields
    is_paid: bool = False,
    paid_amount: float = None,
    cash_bank_account: str = None,
    mode_of_payment: str = None,
    # Submission control
    do_not_submit: bool = False,
) -> dict:
    """
    Create a new Purchase Invoice.
    Works for both eTIMS-registered and non-registered users.
    
    Args:
        supplier: Supplier name or ID
        company: Company name
        items: List of items with fields: item_code, qty, rate, warehouse (optional)
        posting_date: Posting date (defaults to today)
        bill_no: Supplier bill number
        bill_date: Supplier bill date
        branch: Branch name
        warehouse: Default warehouse for items
        currency: Currency code (defaults to company currency)
        taxes: List of tax entries
        update_stock: Whether to update stock on submission
        prevent_etims_submission: Prevent submission to eTIMS even if registered
        settings_name: Specific eTIMS settings name (optional)
        is_paid: Whether the invoice is paid immediately (default: False)
        paid_amount: Amount paid (required if is_paid=True, defaults to grand_total)
        cash_bank_account: Cash/Bank account for payment (required if is_paid=True)
        mode_of_payment: Mode of payment name (optional, e.g., "Cash", "Bank")
        do_not_submit: If True, invoice will be saved as draft only (default: False)
    
    Returns:
        dict: Created purchase invoice details
    """
    try:
        # Check if eTIMS is registered
        settings_doc = get_settings(company_name=company, settings_name=settings_name)
        has_etims = settings_doc is not None and not prevent_etims_submission
        
        # Create purchase invoice
        purchase_invoice = frappe.new_doc("Purchase Invoice")
        purchase_invoice.supplier = supplier
        purchase_invoice.company = company
        purchase_invoice.update_stock = update_stock
        purchase_invoice.prevent_etims_submission = prevent_etims_submission or not has_etims
        
        if posting_date:
            purchase_invoice.posting_date = posting_date
        if bill_no:
            purchase_invoice.bill_no = bill_no
        if bill_date:
            purchase_invoice.bill_date = bill_date
        if branch:
            purchase_invoice.branch = branch
        if warehouse:
            purchase_invoice.set_warehouse = warehouse
        if currency:
            purchase_invoice.currency = currency
        
        # Add items
        for item_data in items:
            item_row = purchase_invoice.append("items", {
                "item_code": item_data.get("item_code"),
                "qty": item_data.get("qty", 1),
                "rate": item_data.get("rate", 0),
                "warehouse": item_data.get("warehouse") or warehouse,
            })
            
            # Add eTIMS-specific fields if available
            if has_etims and item_data.get("custom_item_classification"):
                item_row.custom_item_classification = item_data.get("custom_item_classification")
            if has_etims and item_data.get("custom_packaging_unit"):
                item_row.custom_packaging_unit = item_data.get("custom_packaging_unit")
            if has_etims and item_data.get("custom_unit_of_quantity"):
                item_row.custom_unit_of_quantity = item_data.get("custom_unit_of_quantity")
            if has_etims and item_data.get("custom_taxation_type"):
                item_row.custom_taxation_type = item_data.get("custom_taxation_type")
        
        # Add taxes if provided
        if taxes:
            for tax_data in taxes:
                purchase_invoice.append("taxes", tax_data)
        
        purchase_invoice.insert()
        
        # Handle cash payment if is_paid is True
        if is_paid:
            if not cash_bank_account:
                return {
                    "success": False,
                    "message": "cash_bank_account is required when is_paid=True",
                }
            
            # Set payment fields
            purchase_invoice.is_paid = 1
            purchase_invoice.cash_bank_account = cash_bank_account
            
            if paid_amount is not None:
                purchase_invoice.paid_amount = paid_amount
            else:
                # Default to grand_total if paid_amount not specified
                purchase_invoice.paid_amount = purchase_invoice.grand_total
            
            if mode_of_payment:
                purchase_invoice.mode_of_payment = mode_of_payment
            
            # Calculate base_paid_amount
            purchase_invoice.base_paid_amount = purchase_invoice.paid_amount * purchase_invoice.conversion_rate
            
            # Calculate outstanding amount
            purchase_invoice.outstanding_amount = max(0, purchase_invoice.grand_total - purchase_invoice.paid_amount)
            
            purchase_invoice.save()
        
        # Submit the invoice unless do_not_submit is True
        if not do_not_submit:
            purchase_invoice.submit()
            # Reload to get updated values after submission
            purchase_invoice.reload()
        
        return {
            "success": True,
            "message": "Purchase Invoice created successfully",
            "name": purchase_invoice.name,
            "docstatus": purchase_invoice.docstatus,
            "has_etims": has_etims,
            "etims_submission": "enabled" if has_etims else "disabled",
            "is_paid": is_paid,
            "paid_amount": purchase_invoice.paid_amount if is_paid else 0,
            "outstanding_amount": purchase_invoice.outstanding_amount if is_paid else purchase_invoice.grand_total,
        }
    except Exception as e:
        frappe.log_error(f"Error creating purchase invoice: {str(e)}", "Purchase Invoice Creation Error")
        return {
            "success": False,
            "message": f"Error creating purchase invoice: {str(e)}",
        }


@frappe.whitelist()
def create_purchase_receipt(
    supplier: str,
    company: str,
    items: list,
    posting_date: str = None,
    supplier_delivery_note: str = None,
    branch: str = None,
    warehouse: str = None,
    currency: str = None,
    taxes: list = None,
    purchase_order: str = None,
    do_not_submit: bool = False,
) -> dict:
    """
    Create a new Purchase Receipt.
    
    Args:
        supplier: Supplier name or ID
        company: Company name
        items: List of items with fields: item_code, qty, rate, warehouse (optional), purchase_order_item (optional), provisional_expense_account (optional)
        posting_date: Posting date (defaults to today)
        supplier_delivery_note: Supplier delivery note number (optional)
        branch: Branch name (optional)
        warehouse: Default warehouse for items (optional)
        currency: Currency code (defaults to company currency)
        taxes: List of tax entries (optional)
        purchase_order: Purchase Order name to link (optional)
        do_not_submit: If True, receipt will be saved as draft only (default: False)
    
    Returns:
        dict: Created purchase receipt details
    """
    try:
        # Check if provisional accounting is enabled and validate default_provisional_account
        is_valid, error_dict, default_provisional_account = validate_and_get_provisional_account(
            company=company,
            auto_fix=False
        )
        
        if not is_valid:
            return error_dict
        
        # Get provisional accounting status for later use (if account is set, accounting is enabled)
        enable_provisional_accounting = bool(default_provisional_account)
        
        # Create purchase receipt
        purchase_receipt = frappe.new_doc("Purchase Receipt")
        purchase_receipt.supplier = supplier
        purchase_receipt.company = company
        
        if posting_date:
            purchase_receipt.posting_date = posting_date
        if supplier_delivery_note:
            purchase_receipt.supplier_delivery_note = supplier_delivery_note
        if branch:
            purchase_receipt.branch = branch
        if warehouse:
            purchase_receipt.set_warehouse = warehouse
        if currency:
            purchase_receipt.currency = currency
        if purchase_order:
            purchase_receipt.purchase_order = purchase_order
        
        # Add items
        for item_data in items:
            item_code = item_data.get("item_code")
            
            # Check if item is a non-stock item (for provisional accounting)
            is_stock_item = frappe.db.get_value("Item", item_code, "is_stock_item")
            
            item_row = purchase_receipt.append("items", {
                "item_code": item_code,
                "qty": item_data.get("qty", 1),
                "received_qty": item_data.get("received_qty") or item_data.get("qty", 1),
                "rejected_qty": item_data.get("rejected_qty", 0),
                "rate": item_data.get("rate", 0),
                "warehouse": item_data.get("warehouse") or warehouse,
            })
            
            # Set provisional expense account if provided or if needed for non-stock items
            if item_data.get("provisional_expense_account"):
                item_row.provisional_expense_account = item_data.get("provisional_expense_account")
            elif enable_provisional_accounting and not is_stock_item:
                # For non-stock items with provisional accounting enabled, set the default
                if default_provisional_account:
                    item_row.provisional_expense_account = default_provisional_account
            
            # Link to purchase order item if provided
            if item_data.get("purchase_order_item"):
                item_row.purchase_order_item = item_data.get("purchase_order_item")
            if purchase_order:
                item_row.purchase_order = purchase_order
        
        # Add taxes if provided
        if taxes:
            for tax_data in taxes:
                purchase_receipt.append("taxes", tax_data)
        
        purchase_receipt.insert()
        
        # Submit the receipt unless do_not_submit is True
        if not do_not_submit:
            purchase_receipt.submit()
            # Reload to get updated values after submission
            purchase_receipt.reload()
        
        return {
            "success": True,
            "message": "Purchase Receipt created successfully",
            "name": purchase_receipt.name,
            "docstatus": purchase_receipt.docstatus,
            "grand_total": purchase_receipt.grand_total,
            "status": purchase_receipt.status,
        }
    except frappe.ValidationError as e:
        # Handle validation errors specifically
        error_message = str(e)
        if "provisional" in error_message.lower() or "default_provisional_account" in error_message.lower():
            return {
                "success": False,
                "message": f"Provisional accounting configuration error: {error_message}. Please ensure 'Default Provisional Account' is set in Company '{company}' settings.",
                "error_type": "provisional_accounting_error",
                "company": company,
            }
        frappe.log_error(f"Validation error creating purchase receipt: {str(e)}", "Purchase Receipt Creation Validation Error")
        return {
            "success": False,
            "message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        frappe.log_error(f"Error creating purchase receipt: {str(e)}", "Purchase Receipt Creation Error")
        return {
            "success": False,
            "message": f"Error creating purchase receipt: {str(e)}",
        }


@frappe.whitelist()
def update_purchase_invoice(
    name: str,
    items: list = None,
    posting_date: str = None,
    bill_no: str = None,
    bill_date: str = None,
    taxes: list = None,
    prevent_etims_submission: bool = None,
) -> dict:
    """
    Update an existing Purchase Invoice.
    
    Args:
        name: Purchase Invoice name/ID
        items: Updated list of items (optional)
        posting_date: Updated posting date (optional)
        bill_no: Updated bill number (optional)
        bill_date: Updated bill date (optional)
        taxes: Updated tax entries (optional)
        prevent_etims_submission: Update eTIMS submission flag (optional)
    
    Returns:
        dict: Updated purchase invoice details
    """
    try:
        purchase_invoice = frappe.get_doc("Purchase Invoice", name)
        
        if purchase_invoice.docstatus == 1:
            return {
                "success": False,
                "message": "Cannot update a submitted Purchase Invoice. Please cancel it first.",
            }
        
        if posting_date:
            purchase_invoice.posting_date = posting_date
        if bill_no:
            purchase_invoice.bill_no = bill_no
        if bill_date:
            purchase_invoice.bill_date = bill_date
        if prevent_etims_submission is not None:
            purchase_invoice.prevent_etims_submission = prevent_etims_submission
        
        if items:
            purchase_invoice.set("items", [])
            for item_data in items:
                purchase_invoice.append("items", {
                    "item_code": item_data.get("item_code"),
                    "qty": item_data.get("qty", 1),
                    "rate": item_data.get("rate", 0),
                    "warehouse": item_data.get("warehouse"),
                })
        
        if taxes:
            purchase_invoice.set("taxes", [])
            for tax_data in taxes:
                purchase_invoice.append("taxes", tax_data)
        
        purchase_invoice.save()
        
        return {
            "success": True,
            "message": "Purchase Invoice updated successfully",
            "name": purchase_invoice.name,
        }
    except Exception as e:
        frappe.log_error(f"Error updating purchase invoice: {str(e)}", "Purchase Invoice Update Error")
        return {
            "success": False,
            "message": f"Error updating purchase invoice: {str(e)}",
        }


@frappe.whitelist()
def get_purchase_invoice(name: str) -> dict:
    """
    Get details of a Purchase Invoice.
    
    Args:
        name: Purchase Invoice name/ID
    
    Returns:
        dict: Purchase Invoice details
    """
    try:
        purchase_invoice = frappe.get_doc("Purchase Invoice", name)
        settings_doc = get_settings(company_name=purchase_invoice.company)
        
        return {
            "success": True,
            "data": {
                "name": purchase_invoice.name,
                "supplier": purchase_invoice.supplier,
                "supplier_name": purchase_invoice.supplier_name,
                "company": purchase_invoice.company,
                "posting_date": str(purchase_invoice.posting_date),
                "bill_no": purchase_invoice.bill_no,
                "bill_date": str(purchase_invoice.bill_date) if purchase_invoice.bill_date else None,
                "grand_total": purchase_invoice.grand_total,
                "total_taxes_and_charges": purchase_invoice.total_taxes_and_charges,
                "outstanding_amount": purchase_invoice.outstanding_amount,
                "status": purchase_invoice.status,
                "docstatus": purchase_invoice.docstatus,
                "has_etims": settings_doc is not None,
                "prevent_etims_submission": getattr(purchase_invoice, "prevent_etims_submission", False),
                "custom_slade_id": getattr(purchase_invoice, "custom_slade_id", None),
                "items": [
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "qty": item.qty,
                        "rate": item.rate,
                        "amount": item.amount,
                        "warehouse": item.warehouse,
                    }
                    for item in purchase_invoice.items
                ],
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching purchase invoice: {str(e)}",
        }


@frappe.whitelist()
def list_purchase_invoices(
    supplier: str = None,
    company: str = None,
    from_date: str = None,
    to_date: str = None,
    status: str = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """
    List Purchase Invoices with optional filters.
    
    Args:
        supplier: Filter by supplier (optional)
        company: Filter by company (optional)
        from_date: Filter from date (optional)
        to_date: Filter to date (optional)
        status: Filter by status (optional)
        limit: Number of records to return
        offset: Offset for pagination
    
    Returns:
        dict: List of purchase invoices
    """
    try:
        filters = {}
        
        if supplier:
            filters["supplier"] = supplier
        if company:
            filters["company"] = company
        if from_date:
            filters["posting_date"] = [">=", from_date]
        if to_date:
            if "posting_date" in filters:
                filters["posting_date"] = ["between", [from_date or "2000-01-01", to_date]]
            else:
                filters["posting_date"] = ["<=", to_date]
        if status:
            filters["status"] = status
        
        purchase_invoices = frappe.get_all(
            "Purchase Invoice",
            filters=filters,
            fields=[
                "name",
                "supplier",
                "supplier_name",
                "company",
                "posting_date",
                "bill_no",
                "grand_total",
                "status",
                "docstatus",
            ],
            limit=limit,
            start=offset,
            order_by="posting_date desc",
        )
        
        return {
            "success": True,
            "data": purchase_invoices,
            "count": len(purchase_invoices),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing purchase invoices: {str(e)}",
        }


@frappe.whitelist()
def list_purchase_receipts(
    supplier: str = None,
    company: str = None,
    warehouse: str = None,
    item_code: str = None,
    from_date: str = None,
    to_date: str = None,
    status: str = None,
    docstatus: int = 1,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """
    List Purchase Receipts with optional filters.
    
    Args:
        supplier: Filter by supplier (optional)
        company: Filter by company (optional)
        warehouse: Filter by warehouse (optional)
        item_code: Filter by item code (optional)
        from_date: Filter from date (optional, format: YYYY-MM-DD)
        to_date: Filter to date (optional, format: YYYY-MM-DD)
        status: Filter by status (optional)
        docstatus: Document status (0=Draft, 1=Submitted, 2=Cancelled, default: 1)
        limit: Number of records to return (default: 20)
        offset: Offset for pagination (default: 0)
    
    Returns:
        dict: List of purchase receipts with items
    """
    try:
        filters = {}
        
        if supplier:
            filters["supplier"] = supplier
        if company:
            filters["company"] = company
        if from_date:
            filters["posting_date"] = [">=", from_date]
        if to_date:
            if "posting_date" in filters:
                filters["posting_date"] = ["between", [from_date or "2000-01-01", to_date]]
            else:
                filters["posting_date"] = ["<=", to_date]
        if status:
            filters["status"] = status
        if docstatus is not None:
            filters["docstatus"] = docstatus
        
        purchase_receipts = frappe.get_all(
            "Purchase Receipt",
            filters=filters,
            fields=[
                "name",
                "supplier",
                "supplier_name",
                "company",
                "posting_date",
                "posting_time",
                "grand_total",
                "status",
                "docstatus",
                "per_billed",
                "is_return",
            ],
            limit=limit,
            start=offset,
            order_by="posting_date desc, posting_time desc",
        )
        
        # If warehouse or item_code filter, need to filter by items
        if warehouse or item_code:
            filtered_receipts = []
            for receipt in purchase_receipts:
                # Get items for this purchase receipt
                item_filters = {"parent": receipt["name"]}
                if item_code:
                    item_filters["item_code"] = item_code
                
                items = frappe.get_all(
                    "Purchase Receipt Item",
                    filters=item_filters,
                    fields=[
                        "item_code",
                        "item_name",
                        "qty",
                        "received_qty",
                        "rejected_qty",
                        "warehouse",
                        "rate",
                        "amount",
                        "purchase_order",
                        "purchase_invoice",
                    ],
                )
                
                # Filter by warehouse if specified
                if warehouse:
                    items = [item for item in items if item.get("warehouse") == warehouse]
                
                if items:
                    receipt["items"] = items
                    filtered_receipts.append(receipt)
            
            purchase_receipts = filtered_receipts
        else:
            # Get items for each receipt if not already filtered
            for receipt in purchase_receipts:
                items = frappe.get_all(
                    "Purchase Receipt Item",
                    filters={"parent": receipt["name"]},
                    fields=[
                        "item_code",
                        "item_name",
                        "qty",
                        "received_qty",
                        "rejected_qty",
                        "warehouse",
                        "rate",
                        "amount",
                        "purchase_order",
                        "purchase_invoice",
                    ],
                )
                receipt["items"] = items
        
        return {
            "success": True,
            "data": purchase_receipts,
            "count": len(purchase_receipts),
        }
    except Exception as e:
        frappe.log_error(f"Error listing purchase receipts: {str(e)}", "List Purchase Receipts Error")
        return {
            "success": False,
            "message": f"Error listing purchase receipts: {str(e)}",
        }


@frappe.whitelist()
def get_purchase_receipt(name: str) -> dict:
    """
    Get detailed information about a specific Purchase Receipt.
    
    Args:
        name: Purchase Receipt name/ID
    
    Returns:
        dict: Detailed purchase receipt information including all items
    """
    try:
        if not frappe.db.exists("Purchase Receipt", name):
            return {
                "success": False,
                "message": f"Purchase Receipt '{name}' does not exist",
            }
        
        purchase_receipt = frappe.get_doc("Purchase Receipt", name)
        
        # Get all items
        items = []
        for item in purchase_receipt.items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "received_qty": item.received_qty,
                "rejected_qty": item.rejected_qty,
                "warehouse": item.warehouse,
                "rate": item.rate,
                "amount": item.amount,
                "purchase_order": item.purchase_order,
                "purchase_order_item": item.purchase_order_item,
                "purchase_invoice": item.purchase_invoice,
                "purchase_invoice_item": item.purchase_invoice_item,
            })
        
        return {
            "success": True,
            "data": {
                "name": purchase_receipt.name,
                "supplier": purchase_receipt.supplier,
                "supplier_name": purchase_receipt.supplier_name,
                "company": purchase_receipt.company,
                "posting_date": str(purchase_receipt.posting_date),
                "posting_time": str(purchase_receipt.posting_time) if purchase_receipt.posting_time else None,
                "grand_total": purchase_receipt.grand_total,
                "status": purchase_receipt.status,
                "docstatus": purchase_receipt.docstatus,
                "per_billed": purchase_receipt.per_billed,
                "is_return": purchase_receipt.is_return,
                "items": items,
                "items_count": len(items),
            },
        }
    except Exception as e:
        frappe.log_error(f"Error getting purchase receipt: {str(e)}", "Get Purchase Receipt Error")
        return {
            "success": False,
            "message": f"Error getting purchase receipt: {str(e)}",
        }


@frappe.whitelist()
def submit_purchase_invoice_to_etims(name: str, settings_name: str = None) -> dict:
    """
    Submit a Purchase Invoice to eTIMS.
    Only works if eTIMS is registered for the company.
    
    Args:
        name: Purchase Invoice name/ID
        settings_name: Specific eTIMS settings name (optional)
    
    Returns:
        dict: Submission result
    """
    try:
        purchase_invoice = frappe.get_doc("Purchase Invoice", name)
        
        if purchase_invoice.docstatus != 1:
            return {
                "success": False,
                "message": "Purchase Invoice must be submitted before sending to eTIMS",
            }
        
        settings_doc = get_settings(company_name=purchase_invoice.company, settings_name=settings_name)
        
        if not settings_doc:
            return {
                "success": False,
                "message": "eTIMS is not registered for this company",
                "has_etims": False,
            }
        
        if purchase_invoice.prevent_etims_submission:
            return {
                "success": False,
                "message": "eTIMS submission is prevented for this invoice",
            }
        
        # Submit to eTIMS
        from ..overrides.server.purchase_invoice import submit_purchase_invoice
        submit_purchase_invoice(purchase_invoice)
        
        return {
            "success": True,
            "message": "Purchase Invoice submitted to eTIMS successfully",
            "name": purchase_invoice.name,
        }
    except Exception as e:
        frappe.log_error(f"Error submitting purchase invoice to eTIMS: {str(e)}", "Purchase Invoice eTIMS Submission Error")
        return {
            "success": False,
            "message": f"Error submitting to eTIMS: {str(e)}",
        }


@frappe.whitelist()
def cancel_purchase_invoice(name: str) -> dict:
    """
    Cancel a Purchase Invoice.
    
    Args:
        name: Purchase Invoice name/ID
    
    Returns:
        dict: Cancellation result
    """
    try:
        purchase_invoice = frappe.get_doc("Purchase Invoice", name)
        
        if purchase_invoice.docstatus == 2:
            return {
                "success": False,
                "message": "Purchase Invoice is already cancelled",
            }
        
        purchase_invoice.cancel()
        
        return {
            "success": True,
            "message": "Purchase Invoice cancelled successfully",
            "name": purchase_invoice.name,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error cancelling purchase invoice: {str(e)}",
        }


@frappe.whitelist()
def fetch_registered_purchases(
    company: str = None,
    from_date: str = None,
    to_date: str = None,
    supplier_pin: str = None,
    settings_name: str = None,
) -> dict:
    """
    Fetch registered purchases from eTIMS.
    Only works if eTIMS is registered.
    
    Args:
        company: Company name (optional)
        from_date: Start date for search (optional)
        to_date: End date for search (optional)
        supplier_pin: Supplier PIN to filter (optional)
        settings_name: Specific eTIMS settings name (optional)
    
    Returns:
        dict: Fetch result
    """
    try:
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        settings_doc = get_settings(company_name=company, settings_name=settings_name)
        
        if not settings_doc:
            return {
                "success": False,
                "message": "eTIMS is not registered for this company",
                "has_etims": False,
            }
        
        request_data = {
            "company_name": company,
        }
        
        if from_date:
            request_data["from_date"] = from_date
        if to_date:
            request_data["to_date"] = to_date
        if supplier_pin:
            request_data["supplier_pin"] = supplier_pin
        
        # This will trigger the search and create registered purchase documents
        perform_purchases_search(json.dumps(request_data))
        
        return {
            "success": True,
            "message": "Fetching registered purchases from eTIMS. This may take a few moments.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching registered purchases: {str(e)}",
        }


@frappe.whitelist()
def list_registered_purchases(
    company: str = None,
    supplier_name: str = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """
    List Registered Purchases from eTIMS.
    
    Args:
        company: Filter by company (optional)
        supplier_name: Filter by supplier name (optional)
        from_date: Filter from date (optional)
        to_date: Filter to date (optional)
        limit: Number of records to return
        offset: Offset for pagination
    
    Returns:
        dict: List of registered purchases
    """
    try:
        filters = {}
        
        if company:
            filters["company"] = company
        if supplier_name:
            filters["supplier_name"] = ["like", f"%{supplier_name}%"]
        if from_date:
            filters["sales_date"] = [">=", from_date]
        if to_date:
            if "sales_date" in filters:
                filters["sales_date"] = ["between", [from_date or "2000-01-01", to_date]]
            else:
                filters["sales_date"] = ["<=", to_date]
        
        registered_purchases = frappe.get_all(
            REGISTERED_PURCHASES_DOCTYPE_NAME,
            filters=filters,
            fields=[
                "name",
                "supplier_name",
                "supplier_pin",
                "supplier_invoice_number",
                "sales_date",
                "total_amount",
                "total_tax_amount",
                "workflow_state",
                "can_send_to_etims",
            ],
            limit=limit,
            start=offset,
            order_by="sales_date desc",
        )
        
        return {
            "success": True,
            "data": registered_purchases,
            "count": len(registered_purchases),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing registered purchases: {str(e)}",
        }


@frappe.whitelist()
def create_purchase_invoice_from_registered_purchase(
    registered_purchase_name: str,
    company: str = None,
    warehouse: str = None,
) -> dict:
    """
    Create a Purchase Invoice from a Registered Purchase.
    
    Args:
        registered_purchase_name: Registered Purchase document name
        company: Company name (optional, defaults to registered purchase company)
        warehouse: Warehouse for items (optional)
    
    Returns:
        dict: Created purchase invoice details
    """
    try:
        registered_purchase = frappe.get_doc(REGISTERED_PURCHASES_DOCTYPE_NAME, registered_purchase_name)
        
        if not company:
            company = registered_purchase.organisation or frappe.defaults.get_user_default("Company")
        
        # Prepare data for existing function
        data = {
            "supplier_name": registered_purchase.supplier_name,
            "supplier_pin": registered_purchase.supplier_pin,
            "supplier_branch_id": registered_purchase.supplier_branch_id,
            "supplier_invoice_no": registered_purchase.supplier_invoice_number,
            "supplier_invoice_date": str(registered_purchase.sales_date) if registered_purchase.sales_date else None,
            "company_name": company,
            "branch": registered_purchase.branch,
            "organisation": registered_purchase.organisation,
            "items": [],
        }
        
        # Get items from registered purchase
        for item in registered_purchase.items:
            data["items"].append({
                "item_name": item.item_name,
                "item_code": item.item_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "item_classification_code": item.item_classification_code_data,
                "packaging_unit_code": item.packaging_unit_code,
                "quantity_unit_code": item.quantity_unit_code,
                "taxation_type_code": item.taxation_type_code,
            })
        
        # Use existing function to create purchase invoice
        create_purchase_invoice_from_request(json.dumps(data))
        
        return {
            "success": True,
            "message": "Purchase Invoice created from Registered Purchase successfully",
        }
    except Exception as e:
        frappe.log_error(f"Error creating purchase invoice from registered purchase: {str(e)}", "Purchase Invoice Creation Error")
        return {
            "success": False,
            "message": f"Error creating purchase invoice: {str(e)}",
        }


@frappe.whitelist()
def bulk_submit_purchase_invoices(
    purchase_invoice_names: list,
    settings_name: str = None,
) -> dict:
    """
    Bulk submit multiple Purchase Invoices to eTIMS.
    
    Args:
        purchase_invoice_names: List of Purchase Invoice names/IDs
        settings_name: Specific eTIMS settings name (optional)
    
    Returns:
        dict: Bulk submission result
    """
    try:
        submitted = []
        failed = []
        
        for name in purchase_invoice_names:
            result = submit_purchase_invoice_to_etims(name, settings_name)
            if result.get("success"):
                submitted.append(name)
            else:
                failed.append({"name": name, "error": result.get("message")})
        
        return {
            "success": True,
            "submitted": submitted,
            "failed": failed,
            "total": len(purchase_invoice_names),
            "submitted_count": len(submitted),
            "failed_count": len(failed),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in bulk submission: {str(e)}",
        }


@frappe.whitelist()
def create_purchase_return(
    return_against: str,
    items: list,
    posting_date: str = None,
    company: str = None,
) -> dict:
    """
    Create a Purchase Return (Credit Note).
    
    Args:
        return_against: Original Purchase Invoice name/ID
        items: List of items to return with fields: item_code, qty, rate
        posting_date: Posting date (optional)
        company: Company name (optional)
    
    Returns:
        dict: Created purchase return details
    """
    try:
        original_invoice = frappe.get_doc("Purchase Invoice", return_against)
        
        if not company:
            company = original_invoice.company
        
        # Create return invoice
        return_invoice = frappe.new_doc("Purchase Invoice")
        return_invoice.is_return = 1
        return_invoice.return_against = return_against
        return_invoice.supplier = original_invoice.supplier
        return_invoice.company = company
        
        if posting_date:
            return_invoice.posting_date = posting_date
        
        # Add return items
        for item_data in items:
            return_invoice.append("items", {
                "item_code": item_data.get("item_code"),
                "qty": -abs(item_data.get("qty", 1)),  # Negative quantity for returns
                "rate": item_data.get("rate", 0),
                "warehouse": item_data.get("warehouse"),
            })
        
        return_invoice.insert()
        
        return {
            "success": True,
            "message": "Purchase Return created successfully",
            "name": return_invoice.name,
            "return_against": return_against,
        }
    except Exception as e:
        frappe.log_error(f"Error creating purchase return: {str(e)}", "Purchase Return Creation Error")
        return {
            "success": False,
            "message": f"Error creating purchase return: {str(e)}",
        }


@frappe.whitelist()
def check_etims_registration_status(company: str = None) -> dict:
    """
    Check if eTIMS is registered for a company.
    
    Args:
        company: Company name (optional, defaults to user's default company)
    
    Returns:
        dict: eTIMS registration status
    """
    try:
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        settings_doc = get_settings(company_name=company)
        
        return {
            "success": True,
            "company": company,
            "has_etims": settings_doc is not None,
            "settings_name": settings_doc.name if settings_doc else None,
            "is_active": settings_doc.is_active if settings_doc else False,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error checking eTIMS status: {str(e)}",
        }


# ============================================================================
# BANK AND ACCOUNT MANAGEMENT ENDPOINTS
# ============================================================================

@frappe.whitelist()
def create_cash_or_bank_account(
    account_name: str,
    company: str,
    account_type: str,
    parent_account: str = None,
    account_number: str = None,
    account_currency: str = None,
    is_group: bool = False,
) -> dict:
    """
    Create a Cash or Bank Account.
    
    Args:
        account_name: Name of the account
        company: Company name
        account_type: Account type ("Cash" or "Bank")
        parent_account: Parent account name (optional, will auto-detect if not provided)
        account_number: Account number (optional)
        account_currency: Currency code (optional, defaults to company currency)
        is_group: Whether this is a group account (default: False)
    
    Returns:
        dict: Created account details
    """
    try:
        if account_type not in ["Cash", "Bank"]:
            return {
                "success": False,
                "message": "account_type must be 'Cash' or 'Bank'",
            }
        
        # Check if account already exists
        existing = frappe.db.exists("Account", {
            "account_name": account_name,
            "company": company,
            "account_type": account_type,
        })
        
        if existing:
            return {
                "success": False,
                "message": f"Account '{account_name}' already exists for company '{company}'",
                "name": existing,
            }
        
        # Get or create parent account if not provided
        if not parent_account:
            if account_type == "Cash":
                parent_account = frappe.db.get_value(
                    "Account",
                    {"account_type": "Cash", "is_group": 1, "company": company},
                    "name",
                )
                if not parent_account:
                    # Try to find "Cash In Hand" or create it
                    parent_account = frappe.db.get_value(
                        "Account",
                        {"account_name": "Cash In Hand", "company": company},
                        "name",
                    )
            elif account_type == "Bank":
                parent_account = frappe.db.get_value(
                    "Account",
                    {"account_type": "Bank", "is_group": 1, "company": company},
                    "name",
                )
                if not parent_account:
                    parent_account = frappe.db.get_value(
                        "Account",
                        {"account_name": "Bank Accounts", "company": company},
                        "name",
                    )
        
        if not parent_account:
            return {
                "success": False,
                "message": f"Could not find parent account for {account_type}. Please create it first or specify parent_account.",
            }
        
        # Get company currency if not provided
        if not account_currency:
            account_currency = frappe.get_value("Company", company, "default_currency")
        
        # Create account
        account = frappe.new_doc("Account")
        account.account_name = account_name
        account.company = company
        account.account_type = account_type
        account.parent_account = parent_account
        account.is_group = 1 if is_group else 0
        
        if account_number:
            account.account_number = account_number
        if account_currency:
            account.account_currency = account_currency
        
        # Set root type based on account type
        account.root_type = "Asset"
        account.report_type = "Balance Sheet"
        
        account.insert()
        
        return {
            "success": True,
            "message": f"{account_type} account created successfully",
            "name": account.name,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "company": account.company,
        }
    except Exception as e:
        frappe.log_error(f"Error creating account: {str(e)}", "Account Creation Error")
        return {
            "success": False,
            "message": f"Error creating account: {str(e)}",
        }


@frappe.whitelist()
def list_cash_and_bank_accounts(
    company: str = None,
    account_type: str = None,
    include_disabled: bool = False,
) -> dict:
    """
    List Cash and Bank accounts.
    
    Args:
        company: Filter by company (optional)
        account_type: Filter by account type ("Cash" or "Bank", optional)
        include_disabled: Include disabled accounts (default: False)
    
    Returns:
        dict: List of accounts
    """
    try:
        if not company:
            company = frappe.defaults.get_user_default("Company")
        
        filters = {
            "company": company,
            "account_type": ["in", ["Cash", "Bank"]],
            "is_group": 0,  # Only return ledger accounts, not groups
        }
        
        if account_type:
            filters["account_type"] = account_type
        
        if not include_disabled:
            filters["disabled"] = 0
        
        accounts = frappe.get_all(
            "Account",
            filters=filters,
            fields=[
                "name",
                "account_name",
                "account_type",
                "account_number",
                "account_currency",
                "parent_account",
                "disabled",
                "company",
            ],
            order_by="account_type, account_name",
        )
        
        return {
            "success": True,
            "data": accounts,
            "count": len(accounts),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing accounts: {str(e)}",
        }


@frappe.whitelist()
def get_account_details(name: str) -> dict:
    """
    Get details of a specific account.
    
    Args:
        name: Account name/ID
    
    Returns:
        dict: Account details
    """
    try:
        account = frappe.get_doc("Account", name)
        
        # Get account balance
        GL = DocType("GL Entry")
        
        balance = (
            frappe.qb.from_(GL)
            .select(frappe.qb.functions.Sum(GL.debit - GL.credit).as_("balance"))
            .where(GL.account == account.name)
            .where(GL.is_cancelled == 0)
            .run()
        )
        
        account_balance = balance[0][0] if balance and balance[0][0] else 0.0
        
        return {
            "success": True,
            "data": {
                "name": account.name,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "account_number": account.account_number,
                "account_currency": account.account_currency,
                "company": account.company,
                "parent_account": account.parent_account,
                "is_group": account.is_group,
                "disabled": account.disabled,
                "root_type": account.root_type,
                "report_type": account.report_type,
                "balance": account_balance,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching account details: {str(e)}",
        }


@frappe.whitelist()
def create_bank(
    bank_name: str,
    swift_number: str = None,
) -> dict:
    """
    Create a Bank master record.
    
    Args:
        bank_name: Name of the bank
        swift_number: SWIFT/BIC code (optional)
    
    Returns:
        dict: Created bank details
    """
    try:
        # Check if bank already exists
        existing = frappe.db.exists("Bank", {"name": bank_name})
        
        if existing:
            return {
                "success": False,
                "message": f"Bank '{bank_name}' already exists",
                "name": existing,
            }
        
        bank = frappe.new_doc("Bank")
        bank.bank_name = bank_name
        if swift_number:
            bank.swift_number = swift_number
        
        bank.insert()
        
        return {
            "success": True,
            "message": "Bank created successfully",
            "name": bank.name,
            "bank_name": bank.bank_name,
        }
    except Exception as e:
        frappe.log_error(f"Error creating bank: {str(e)}", "Bank Creation Error")
        return {
            "success": False,
            "message": f"Error creating bank: {str(e)}",
        }


@frappe.whitelist()
def list_banks() -> dict:
    """
    List all banks.
    
    Returns:
        dict: List of banks
    """
    try:
        banks = frappe.get_all(
            "Bank",
            fields=["name", "bank_name", "swift_number"],
            order_by="bank_name",
        )
        
        return {
            "success": True,
            "data": banks,
            "count": len(banks),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing banks: {str(e)}",
        }


@frappe.whitelist()
def create_bank_account(
    account_name: str,
    bank: str,
    company: str,
    account: str = None,
    account_type: str = None,
    account_subtype: str = None,
    bank_account_no: str = None,
    iban: str = None,
    branch_code: str = None,
    is_company_account: bool = True,
    is_default: bool = False,
) -> dict:
    """
    Create a Bank Account record (links Bank to Account).
    
    Args:
        account_name: Name for the bank account record
        bank: Bank name/ID
        company: Company name
        account: Company Account name/ID (optional, will create if not provided)
        account_type: Bank Account Type (optional)
        account_subtype: Bank Account Subtype (optional)
        bank_account_no: Bank account number (optional)
        iban: IBAN (optional)
        branch_code: Branch code (optional)
        is_company_account: Whether this is a company account (default: True)
        is_default: Whether this is the default account (default: False)
    
    Returns:
        dict: Created bank account details
    """
    try:
        # Check if bank account already exists
        existing = frappe.db.exists("Bank Account", {
            "account_name": account_name,
            "company": company,
        })
        
        if existing:
            return {
                "success": False,
                "message": f"Bank Account '{account_name}' already exists for company '{company}'",
                "name": existing,
            }
        
        # Create account if not provided
        if not account:
            # Create a Bank account
            account_result = create_cash_or_bank_account(
                account_name=account_name,
                company=company,
                account_type="Bank",
            )
            
            if not account_result.get("success"):
                return account_result
            
            account = account_result["name"]
        
        # Verify account exists and is a Bank account
        account_doc = frappe.get_doc("Account", account)
        if account_doc.account_type != "Bank":
            return {
                "success": False,
                "message": f"Account '{account}' is not a Bank account",
            }
        
        # Create bank account
        bank_account = frappe.new_doc("Bank Account")
        bank_account.account_name = account_name
        bank_account.bank = bank
        bank_account.company = company
        bank_account.account = account
        bank_account.is_company_account = 1 if is_company_account else 0
        bank_account.is_default = 1 if is_default else 0
        
        if account_type:
            bank_account.account_type = account_type
        if account_subtype:
            bank_account.account_subtype = account_subtype
        if bank_account_no:
            bank_account.bank_account_no = bank_account_no
        if iban:
            bank_account.iban = iban
        if branch_code:
            bank_account.branch_code = branch_code
        
        bank_account.insert()
        
        return {
            "success": True,
            "message": "Bank Account created successfully",
            "name": bank_account.name,
            "account_name": bank_account.account_name,
            "bank": bank_account.bank,
            "account": bank_account.account,
            "company": bank_account.company,
        }
    except Exception as e:
        frappe.log_error(f"Error creating bank account: {str(e)}", "Bank Account Creation Error")
        return {
            "success": False,
            "message": f"Error creating bank account: {str(e)}",
        }


@frappe.whitelist()
def list_bank_accounts(
    company: str = None,
    bank: str = None,
    is_company_account: bool = None,
) -> dict:
    """
    List Bank Account records.
    
    Args:
        company: Filter by company (optional)
        bank: Filter by bank (optional)
        is_company_account: Filter by company account flag (optional)
    
    Returns:
        dict: List of bank accounts
    """
    try:
        filters = {}
        
        if company:
            filters["company"] = company
        if bank:
            filters["bank"] = bank
        if is_company_account is not None:
            filters["is_company_account"] = 1 if is_company_account else 0
        
        bank_accounts = frappe.get_all(
            "Bank Account",
            filters=filters,
            fields=[
                "name",
                "account_name",
                "bank",
                "account",
                "company",
                "bank_account_no",
                "iban",
                "branch_code",
                "is_company_account",
                "is_default",
                "disabled",
            ],
            order_by="company, account_name",
        )
        
        return {
            "success": True,
            "data": bank_accounts,
            "count": len(bank_accounts),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing bank accounts: {str(e)}",
        }


@frappe.whitelist()
def get_bank_account_details(name: str) -> dict:
    """
    Get details of a specific Bank Account.
    
    Args:
        name: Bank Account name/ID
    
    Returns:
        dict: Bank Account details
    """
    try:
        bank_account = frappe.get_doc("Bank Account", name)
        
        account_details = None
        if bank_account.account:
            account_details = get_account_details(bank_account.account)
        
        return {
            "success": True,
            "data": {
                "name": bank_account.name,
                "account_name": bank_account.account_name,
                "bank": bank_account.bank,
                "account": bank_account.account,
                "company": bank_account.company,
                "bank_account_no": bank_account.bank_account_no,
                "iban": bank_account.iban,
                "branch_code": bank_account.branch_code,
                "account_type": bank_account.account_type,
                "account_subtype": bank_account.account_subtype,
                "is_company_account": bank_account.is_company_account,
                "is_default": bank_account.is_default,
                "disabled": bank_account.disabled,
                "account_details": account_details.get("data") if account_details and account_details.get("success") else None,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching bank account details: {str(e)}",
        }


@frappe.whitelist()
def update_account(
    name: str,
    account_name: str = None,
    account_number: str = None,
    disabled: bool = None,
) -> dict:
    """
    Update an account.
    
    Args:
        name: Account name/ID
        account_name: Updated account name (optional)
        account_number: Updated account number (optional)
        disabled: Update disabled status (optional)
    
    Returns:
        dict: Update result
    """
    try:
        account = frappe.get_doc("Account", name)
        
        if account_name:
            account.account_name = account_name
        if account_number is not None:
            account.account_number = account_number
        if disabled is not None:
            account.disabled = 1 if disabled else 0
        
        account.save()
        
        return {
            "success": True,
            "message": "Account updated successfully",
            "name": account.name,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating account: {str(e)}",
        }

    