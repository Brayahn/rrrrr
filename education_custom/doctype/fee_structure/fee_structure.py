from education.education.doctype.fee_structure.fee_structure import FeeStructure as CoreFeeStructure
from frappe.utils import cstr


class FeeStructure(CoreFeeStructure):

	def autoname(self):
		"""
		Custom naming format: {program}-{academic_term}-{academic_year}-{cost_center}-{student_category}
		"""
		parts = [
			cstr(self.program) or "",
			cstr(self.academic_term) or "",
			cstr(self.academic_year) or "",
			cstr(self.cost_center) or "",
			cstr(self.student_category) or "",
		]
		# Filter out empty parts and join with hyphen
		name_parts = [p for p in parts if p]
		self.name = "-".join(name_parts) if name_parts else None
