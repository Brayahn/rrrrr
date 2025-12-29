import frappe

def get_context(context):
	# do your magic here
	context.read_only = 1

def get_student():
	return frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")

# def student_is_enrolled():

def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related student related to this document"""
	# if get_student():
	return True
	# else:
	# 	print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",get_student(),doc.student)
	# 	return False

