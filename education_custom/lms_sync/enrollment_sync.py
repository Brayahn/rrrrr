import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_sync_enabled,
	log_sync_error,
	get_user_for_student,
	get_lms_course_for_education_course,
)
from education_custom.lms_sync.program_sync import add_member_to_program, remove_member_from_program


def sync_enrollment(doc, method=None):
	"""Sync Program Enrollment to LMS on submit"""
	if not is_sync_enabled(doc):
		return

	try:
		# Get the user for this student
		user = get_user_for_student(doc.student)
		if not user:
			frappe.msgprint(
				_("LMS sync skipped: No user account found for student {0}").format(doc.student_name),
				indicator="orange",
				alert=True
			)
			return

		# Get the LMS program
		program = frappe.get_doc("Program", doc.program)
		if not program.lms_program:
			frappe.msgprint(
				_("LMS sync skipped: Program {0} is not linked to an LMS Program").format(doc.program),
				indicator="orange",
				alert=True
			)
			return

		lms_program = program.lms_program

		# Add user to LMS program members
		add_member_to_program(user, lms_program)

		# Enroll user in all courses of the program
		enroll_in_program_courses(user, doc, lms_program)

		# Mark as synced
		frappe.db.set_value("Program Enrollment", doc.name, "lms_synced", 1, update_modified=False)

		frappe.msgprint(
			_("Student enrolled in LMS Program and courses successfully"),
			indicator="green",
			alert=True
		)

	except Exception as e:
		log_sync_error(doc, e, "sync_enrollment")
		frappe.msgprint(
			_("LMS enrollment sync failed. Check Error Log for details."),
			indicator="red",
			alert=True
		)


def cancel_enrollment(doc, method=None):
	"""Cancel LMS enrollments when Program Enrollment is cancelled"""
	try:
		if not doc.lms_synced:
			return

		# Get the user for this student
		user = get_user_for_student(doc.student)
		if not user:
			return

		# Get the LMS program
		program = frappe.get_doc("Program", doc.program)
		if not program.lms_program:
			return

		# Remove LMS enrollments for this program enrollment
		remove_lms_enrollments(user, doc)

		# Remove from program members
		remove_member_from_program(user, program.lms_program)

		# Mark as not synced
		frappe.db.set_value("Program Enrollment", doc.name, "lms_synced", 0, update_modified=False)

	except Exception as e:
		log_sync_error(doc, e, "cancel_enrollment")


def enroll_in_program_courses(user, program_enrollment, lms_program):
	"""Enroll user in all LMS courses of the program"""
	program_enrollment_doc = frappe.get_doc("Program Enrollment", program_enrollment.name)

	for course_ref in program_enrollment_doc.courses:
		course_name = course_ref.course
		lms_course = get_lms_course_for_education_course(course_name)

		if not lms_course:
			continue

		# Check if course is published
		if not frappe.db.get_value("LMS Course", lms_course, "published"):
			continue

		# Check if already enrolled
		existing = frappe.db.exists("LMS Enrollment", {
			"member": user,
			"course": lms_course
		})

		if existing:
			continue

		# Create LMS enrollment
		enrollment = frappe.get_doc({
			"doctype": "LMS Enrollment",
			"member": user,
			"course": lms_course,
			"member_type": "Student",
			"education_program_enrollment": program_enrollment.name,
			"synced_from_education": 1,
		})
		enrollment.insert(ignore_permissions=True)


def remove_lms_enrollments(user, program_enrollment):
	"""Remove LMS enrollments created from this program enrollment"""
	enrollments = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": user,
			"education_program_enrollment": program_enrollment.name,
			"synced_from_education": 1
		},
		pluck="name"
	)

	for enrollment in enrollments:
		frappe.delete_doc("LMS Enrollment", enrollment, force=True)


@frappe.whitelist()
def resync_enrollment_to_lms(program_enrollment_name):
	"""
	Manually resync a Program Enrollment to LMS.
	This will update the LMS enrollment to match the current state of Program Enrollment.
	"""
	doc = frappe.get_doc("Program Enrollment", program_enrollment_name)

	if doc.docstatus != 1:
		frappe.throw(_("Program Enrollment must be submitted before syncing to LMS"))

	if not is_sync_enabled(doc):
		frappe.throw(_("LMS sync is not enabled"))

	# Get the user for this student
	user = get_user_for_student(doc.student)
	if not user:
		frappe.throw(_("No user account found for student {0}").format(doc.student_name))

	# Get the LMS program
	program = frappe.get_doc("Program", doc.program)
	if not program.lms_program:
		frappe.throw(_("Program {0} is not linked to an LMS Program. Please sync the Program first.").format(doc.program))

	lms_program = program.lms_program

	# Get current courses in Program Enrollment
	enrollment_courses = {c.course for c in doc.courses}

	# Get current LMS enrollments for this user from this program enrollment
	current_lms_enrollments = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": user,
			"education_program_enrollment": doc.name,
			"synced_from_education": 1
		},
		fields=["name", "course"]
	)
	current_lms_courses = {e.course for e in current_lms_enrollments}

	# Get LMS courses that should exist for the education courses
	target_lms_courses = {}
	for course_name in enrollment_courses:
		lms_course = get_lms_course_for_education_course(course_name)
		if lms_course:
			target_lms_courses[lms_course] = course_name

	added = 0
	removed = 0

	# Add missing enrollments
	for lms_course in target_lms_courses:
		if lms_course not in current_lms_courses:
			# Check if course is published
			if not frappe.db.get_value("LMS Course", lms_course, "published"):
				continue

			# Check if already enrolled (maybe from another program)
			existing = frappe.db.exists("LMS Enrollment", {
				"member": user,
				"course": lms_course
			})
			if not existing:
				enrollment = frappe.get_doc({
					"doctype": "LMS Enrollment",
					"member": user,
					"course": lms_course,
					"member_type": "Student",
					"education_program_enrollment": doc.name,
					"synced_from_education": 1,
				})
				enrollment.insert(ignore_permissions=True)
				added += 1

	# Remove enrollments for courses no longer in program enrollment
	for lms_enrollment in current_lms_enrollments:
		if lms_enrollment.course not in target_lms_courses:
			frappe.delete_doc("LMS Enrollment", lms_enrollment.name, force=True)
			removed += 1

	# Ensure user is a program member
	add_member_to_program(user, lms_program)

	# Update sync flag
	frappe.db.set_value("Program Enrollment", doc.name, "lms_synced", 1, update_modified=False)

	return {
		"success": True,
		"added": added,
		"removed": removed,
		"message": _("Sync complete. Added {0} enrollments, removed {1} enrollments.").format(added, removed)
	}


def enroll_student_in_course(student_name, course_name):
	"""
	Utility function to enroll a student in a single LMS course
	Can be called from Course Enrollment if needed
	"""
	user = get_user_for_student(student_name)
	if not user:
		return None

	lms_course = get_lms_course_for_education_course(course_name)
	if not lms_course:
		return None

	# Check if course is published
	if not frappe.db.get_value("LMS Course", lms_course, "published"):
		return None

	# Check if already enrolled
	existing = frappe.db.exists("LMS Enrollment", {
		"member": user,
		"course": lms_course
	})

	if existing:
		return existing

	# Create enrollment
	enrollment = frappe.get_doc({
		"doctype": "LMS Enrollment",
		"member": user,
		"course": lms_course,
		"member_type": "Student",
		"synced_from_education": 1,
	})
	enrollment.insert(ignore_permissions=True)

	return enrollment.name
