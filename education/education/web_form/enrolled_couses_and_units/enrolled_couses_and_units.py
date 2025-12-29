import frappe

def get_context(context):
	# do your magic here
		context.read_only = 1
	
def get_list_context(context):
	context.read_only = 1

	# context.row_template = 'education/templates/includes/program_row_template.html'
	context.get_list = get_course_enrollments
    
    
   
def get_student():
	return frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")



def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related student related to this document"""
	if get_student():
		return True
	else:
		print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",get_student(),doc.student)
		return False




def get_course_enrollments(doctype,txt,filters,limit_start,limit_page_length=20,order_by=None):
		student = get_student()
		# print(".....................",get_student())
		enrolled_courses = frappe.db.sql("""
		SELECT ce.*,c.*
		FROM `tabCourse Enrollment` ce
		INNER JOIN `tabCourse` c ON ce.course = c.name
		WHERE ce.student = %s  order by ce.creation desc
		""",student, as_dict=True)

		
		for course in enrolled_courses:
			parent =course.name
			topic = frappe.db.sql("""SELECT * FROM `tabCourse Topic`
			WHERE parent = %s """,parent, as_dict=True)
			course.topic=topic
		print(enrolled_courses)
		return enrolled_courses
