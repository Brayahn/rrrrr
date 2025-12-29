import frappe


def get_student_for_user(user=None):
	"""Get Student record linked to the current user by email"""
	if not user:
		user = frappe.session.user
	return frappe.db.get_value("Student", {"student_email_id": user}, "name")


# Program Enrollment - Students only see their own enrollments
def program_enrollment_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return f"`tabProgram Enrollment`.student = {frappe.db.escape(student)}"
		return "1=0"  # No access if no student record found
	return ""


def program_enrollment_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		return doc.student == student
	return True


# Course Enrollment - Students only see their own course enrollments
def course_enrollment_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return f"`tabCourse Enrollment`.student = {frappe.db.escape(student)}"
		return "1=0"
	return ""


def course_enrollment_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		return doc.student == student
	return True


# Student - Students only see their own record
def student_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return f"`tabStudent`.name = {frappe.db.escape(student)}"
		return "1=0"
	return ""


def student_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		return doc.name == student
	return True


# Fees - Students only see their own fees
def fees_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return f"`tabFees`.student = {frappe.db.escape(student)}"
		return "1=0"
	return ""


def fees_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		return doc.student == student
	return True


# Course - Students only see courses they are enrolled in
def course_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			# Get courses the student is enrolled in
			return f"""`tabCourse`.name IN (
				SELECT course FROM `tabCourse Enrollment` WHERE student = {frappe.db.escape(student)}
			)"""
		return "1=0"
	return ""


def course_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return frappe.db.exists(
				"Course Enrollment", {"student": student, "course": doc.name}
			)
		return False
	return True


# Program - Students only see programs they are enrolled in
def program_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return f"""`tabProgram`.name IN (
				SELECT program FROM `tabProgram Enrollment` WHERE student = {frappe.db.escape(student)}
			)"""
		return "1=0"
	return ""


def program_has_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user

	if "Student" in frappe.get_roles(user) and "Academics User" not in frappe.get_roles(user):
		student = get_student_for_user(user)
		if student:
			return frappe.db.exists(
				"Program Enrollment", {"student": student, "program": doc.name}
			)
		return False
	return True
