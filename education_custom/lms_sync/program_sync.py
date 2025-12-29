import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_sync_enabled,
	log_sync_error,
	has_lms_program_members,
)
from education_custom.lms_sync.course_sync import sync_course_to_program


def sync_program(doc, method=None):
	"""Sync Education Program to LMS Program on creation"""
	if not is_sync_enabled(doc):
		return

	try:
		lms_program = create_lms_program(doc)
		if lms_program:
			frappe.db.set_value("Program", doc.name, "lms_program", lms_program, update_modified=False)
			# Sync all courses
			sync_program_courses(doc, lms_program)

	except Exception as e:
		log_sync_error(doc, e, "sync_program")


def update_program(doc, method=None):
	"""Update LMS Program when Education Program is updated"""
	if not is_sync_enabled(doc):
		return

	try:
		if doc.lms_program and frappe.db.exists("LMS Program", doc.lms_program):
			update_lms_program(doc)
			# Re-sync courses
			sync_program_courses(doc, doc.lms_program)
		else:
			sync_program(doc, method)

	except Exception as e:
		log_sync_error(doc, e, "update_program")


def delete_program(doc, method=None):
	"""Delete LMS Program when Education Program is deleted"""
	try:
		if doc.lms_program and frappe.db.exists("LMS Program", doc.lms_program):
			# Check for enrolled members
			if has_lms_program_members(doc.lms_program):
				frappe.throw(
					_("Cannot delete Program. The linked LMS Program has enrolled members. "
					  "Please remove LMS program members first or unlink the program."),
					title=_("LMS Program Has Members")
				)

			# Delete the LMS program
			# Note: This will not delete the courses, only the program reference
			frappe.delete_doc("LMS Program", doc.lms_program, force=True)

	except frappe.ValidationError:
		raise
	except Exception as e:
		log_sync_error(doc, e, "delete_program")


def create_lms_program(program_doc):
	"""Create an LMS Program from Education Program, or link to existing one"""
	# First check if an LMS Program already exists with this education_program link
	existing = frappe.db.get_value("LMS Program", {"education_program": program_doc.name}, "name")
	if existing:
		# Update the existing one and return
		lms_program = frappe.get_doc("LMS Program", existing)
		lms_program.title = program_doc.program_name
		lms_program.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lms_program._syncing_from_education = True
		lms_program.save(ignore_permissions=True)
		return existing

	# Check if an LMS Program with the same title exists
	existing_by_title = frappe.db.get_value("LMS Program", {"title": program_doc.program_name}, "name")
	if existing_by_title:
		# Link it to this education program and update
		lms_program = frappe.get_doc("LMS Program", existing_by_title)
		lms_program.education_program = program_doc.name
		lms_program.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lms_program._syncing_from_education = True
		lms_program.save(ignore_permissions=True)
		return existing_by_title

	# Create new LMS Program
	lms_program = frappe.get_doc({
		"doctype": "LMS Program",
		"name": program_doc.program_name,  # Use program name directly to avoid any transformation
		"title": program_doc.program_name,
		"published": 1,  # Auto-publish
		"education_program": program_doc.name,
		"synced_from_education": 1,
	})
	# Set flag to prevent reverse sync loop
	lms_program._syncing_from_education = True
	lms_program.insert(ignore_permissions=True)

	return lms_program.name


def update_lms_program(program_doc):
	"""Update LMS Program from Education Program"""
	# Skip if this update is coming from LMS reverse sync
	if getattr(program_doc, "_syncing_from_lms", False):
		return

	lms_program = frappe.get_doc("LMS Program", program_doc.lms_program)
	lms_program.title = program_doc.program_name

	# Set flag to prevent reverse sync loop
	lms_program._syncing_from_education = True
	lms_program.save(ignore_permissions=True)


def sync_program_courses(program_doc, lms_program_name):
	"""Sync all courses of a program to LMS Program - handles add and remove"""
	program = frappe.get_doc("Program", program_doc.name)

	# Get current education courses in program
	education_courses = [c.course for c in program.courses]

	# Get LMS courses that should be in the program
	target_lms_courses = []
	for course_name in education_courses:
		# Skip if course doesn't exist
		if not frappe.db.exists("Course", course_name):
			frappe.log_error(f"Skipping missing Course: {course_name}", "LMS Sync Warning")
			continue

		try:
			# Sync course to LMS if not already synced
			lms_course = sync_course_to_program(course_name, lms_program_name)
			if lms_course:
				target_lms_courses.append(lms_course)
		except Exception as e:
			frappe.log_error(f"Error syncing Course {course_name}: {str(e)}", "LMS Sync Warning")
			continue

	# Reload LMS program to get latest version after course syncs
	lms_program = frappe.get_doc("LMS Program", lms_program_name)

	# Get current LMS courses in program
	current_lms_courses = [pc.course for pc in lms_program.program_courses]

	# Track if we need to save
	needs_save = False

	# Add new courses
	for lms_course in target_lms_courses:
		if lms_course not in current_lms_courses:
			lms_program.append("program_courses", {"course": lms_course})
			needs_save = True

	# Remove courses that are no longer in education program
	# Only remove if they were synced from education
	original_count = len(lms_program.program_courses)
	lms_program.program_courses = [
		pc for pc in lms_program.program_courses
		if pc.course in target_lms_courses or not is_synced_course(pc.course)
	]
	if len(lms_program.program_courses) != original_count:
		needs_save = True

	if needs_save:
		lms_program.save(ignore_permissions=True)


def is_synced_course(lms_course_name):
	"""Check if LMS Course was synced from Education"""
	return frappe.db.get_value("LMS Course", lms_course_name, "synced_from_education")


def add_member_to_program(user, lms_program_name):
	"""Add a user as a member to an LMS Program"""
	lms_program = frappe.get_doc("LMS Program", lms_program_name)

	# Check if already a member
	for member in lms_program.program_members:
		if member.member == user:
			return  # Already a member

	lms_program.append("program_members", {
		"member": user,
		"progress": 0
	})
	lms_program.save(ignore_permissions=True)


def remove_member_from_program(user, lms_program_name):
	"""Remove a user from an LMS Program"""
	if not frappe.db.exists("LMS Program", lms_program_name):
		return

	lms_program = frappe.get_doc("LMS Program", lms_program_name)
	lms_program.program_members = [m for m in lms_program.program_members if m.member != user]
	lms_program.save(ignore_permissions=True)
