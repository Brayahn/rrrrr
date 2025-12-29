
import frappe
from frappe import _


def get_context(context):
	context.read_only = 1
	
def get_list_context(context):
	context.read_only = 1

	# context.row_template = 'education/templates/includes/program_row_template.html'
	context.get_list = get_program_enrollments
    
    
   
def get_student():
	return frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")

def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related student related to this document"""
	if doc.student == get_student():
		return True
	else:
		print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",get_student(),doc.student)
		return False


def get_program_enrollments(doctype,txt,filters,limit_start,limit_page_length=20,order_by=None):
		student = get_student()
		enrolled_courses = frappe.db.sql("""
		SELECT name,program, student_name, academic_year
		FROM `tabProgram Enrollment`
		WHERE student = %s AND docstatus =1 order by creation desc
		""",student, as_dict=True)
		return enrolled_courses

	
