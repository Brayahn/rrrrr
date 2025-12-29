# Copyright (c) 2025, Kenya Compliance Via Slade
# License: See license.txt

import frappe
from frappe.model.document import Document


class InventoryItemDetails(Document):
	"""Inventory Item Details - Stores warehouse-level item information"""

	def validate(self):
		"""Validate inventory item details"""
		# Validate item exists
		if not frappe.db.exists("Item", self.item_code):
			frappe.throw(f"Item {self.item_code} does not exist")

		# Validate warehouse exists
		if not frappe.db.exists("Warehouse", self.warehouse):
			frappe.throw(f"Warehouse {self.warehouse} does not exist")

		# Validate company matches warehouse company
		warehouse_company = frappe.db.get_value("Warehouse", self.warehouse, "company")
		if warehouse_company and warehouse_company != self.company:
			frappe.throw(f"Warehouse {self.warehouse} belongs to company {warehouse_company}, not {self.company}")

		# Validate item belongs to company if custom_company is set
		item_company = frappe.db.get_value("Item", self.item_code, "custom_company")
		if item_company and item_company != self.company:
			frappe.throw(f"Item {self.item_code} belongs to company {item_company}, not {self.company}")

		# Validate UOM exists if provided
		if self.unit_of_measure and not frappe.db.exists("UOM", self.unit_of_measure):
			frappe.throw(f"Unit of Measure {self.unit_of_measure} does not exist")

	def before_save(self):
		"""Set company from warehouse if not provided"""
		if not self.company:
			self.company = frappe.db.get_value("Warehouse", self.warehouse, "company")


def get_inventory_item_details(item_code: str, warehouse: str, company: str = None) -> dict:
	"""Get inventory item details for a specific item-warehouse combination"""
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

	return details


def create_or_update_inventory_item_details(
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
	"""Create or update inventory item details"""
	if not company:
		company = frappe.db.get_value("Warehouse", warehouse, "company")
		if not company:
			frappe.throw(f"Company not found for warehouse {warehouse}")

	# Check if exists
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

