# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.model.mapper import get_mapped_doc


class FeeStructure(WebsiteGenerator):
	def validate(self):
		self.calculate_total()
		self.set_route()

	def set_route(self):
		if not self.route:
			self.route = "fee-structures/" + self.name

	def calculate_total(self):
		"""Calculates total amount."""
		self.total_amount = 0
		for d in self.components:
			self.total_amount += d.amount


@frappe.whitelist()
def make_fee_schedule(source_name, target_doc=None):
	return get_mapped_doc(
		"Fee Structure",
		source_name,
		{
			"Fee Structure": {
				"doctype": "Fee Schedule",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Fee Component": {"doctype": "Fee Component"},
		},
		target_doc,
	)
