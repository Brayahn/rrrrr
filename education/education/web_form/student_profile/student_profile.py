
import frappe
from frappe import _

def get_context(context):
	# do your magic here
	pass
	

def get_student():
	return frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")

def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related student related to this document"""
	
	if doc.name == get_student():
		return True
	else:
		return False
