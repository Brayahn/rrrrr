"""
Monkey patches for LMS app to handle Education module content sync.

These patches handle cases where:
1. Course Lesson content field contains markdown instead of JSON (from Education sync)
2. Lesson references point to non-existent lessons
3. Course Lesson on_update throws JSON errors for synced lessons
"""

import json
import frappe


def patched_get_lesson_icon(body, content):
	"""
	Patched version of lms.lms.utils.get_lesson_icon that handles non-JSON content.

	Education module syncs markdown to the body field, but sometimes the content
	field may contain invalid data. This patch gracefully handles JSON parse errors.
	"""
	from lms.lms.md import find_macros

	if content:
		try:
			parsed_content = json.loads(content)
		except (json.JSONDecodeError, TypeError):
			# Content is not valid JSON, fall through to body/macro parsing
			pass
		else:
			for block in parsed_content.get("blocks", []):
				if block.get("type") == "upload":
					file_type = block.get("data", {}).get("file_type", "")
					if file_type and file_type.lower() in ["mp4", "webm", "ogg", "mov"]:
						return "icon-youtube"

				if block.get("type") == "embed" and block.get("data", {}).get("service") in [
					"youtube",
					"vimeo",
					"cloudflareStream",
					"bunnyStream",
				]:
					return "icon-youtube"

				if block.get("type") == "quiz":
					return "icon-quiz"

			return "icon-list"

	# Fall back to parsing body for macros
	if body:
		macros = find_macros(body)
		for macro in macros:
			if macro[0] == "YouTubeVideo" or macro[0] == "Video":
				return "icon-youtube"
			elif macro[0] == "Quiz":
				return "icon-quiz"

	return "icon-list"


def patched_get_lesson_details(chapter, progress=False):
	"""
	Patched version of lms.lms.utils.get_lesson_details that handles missing lessons.

	When lessons are deleted but Lesson References still exist, this patch
	skips the missing lessons instead of throwing an error.
	"""
	from lms.lms.utils import get_progress

	lessons = []
	lesson_list = frappe.get_all(
		"Lesson Reference", {"parent": chapter.name}, ["lesson", "idx"], order_by="idx"
	)
	for row in lesson_list:
		lesson_details = frappe.db.get_value(
			"Course Lesson",
			row.lesson,
			[
				"name",
				"title",
				"include_in_preview",
				"body",
				"creation",
				"youtube",
				"quiz_id",
				"question",
				"file_type",
				"instructor_notes",
				"course",
				"chapter",
				"content",
			],
			as_dict=True,
		)

		# Skip if lesson doesn't exist (deleted or broken reference)
		if not lesson_details:
			continue

		lesson_details.number = f"{chapter.idx}-{row.idx}"
		lesson_details.icon = patched_get_lesson_icon(lesson_details.body, lesson_details.content)

		if progress:
			lesson_details.is_complete = get_progress(lesson_details.course, lesson_details.name)

		lessons.append(lesson_details)
	return lessons


def patched_save_lesson_details_in_quiz(self, content):
	"""
	Patched version of CourseLesson.save_lesson_details_in_quiz that handles non-JSON content.

	Education module syncs markdown to the body field. The content field should
	only contain editor.js JSON format. This patch skips processing if content
	is not valid JSON.
	"""
	try:
		parsed_content = json.loads(content)
	except (json.JSONDecodeError, TypeError):
		# Content is not valid JSON (likely markdown), skip quiz processing
		return

	# Check if parsed content has the expected structure
	if not isinstance(parsed_content, dict) or "blocks" not in parsed_content:
		return

	for block in parsed_content.get("blocks", []):
		if block.get("type") == "quiz":
			quiz = block.get("data", {}).get("quiz")
			if quiz:
				if not frappe.db.exists("LMS Quiz", quiz):
					frappe.throw(frappe._("Invalid Quiz ID in content"))
				frappe.db.set_value(
					"LMS Quiz",
					quiz,
					{
						"course": self.course,
						"lesson": self.name,
					},
				)


@frappe.whitelist()
def patched_get_programs():
	"""
	Patched version of lms.lms.utils.get_programs that includes title field.

	Returns both enrolled and published programs with title for search/display.
	"""
	# Get enrolled programs with title field
	enrolled_programs = frappe.get_all(
		"LMS Program Member", {"member": frappe.session.user}, ["parent as name", "progress"]
	)
	for program in enrolled_programs:
		program.update(
			frappe.db.get_value(
				"LMS Program", program.name, ["name", "title", "course_count", "member_count"], as_dict=True
			) or {}
		)

	# Get published programs with title field
	published_programs = frappe.get_all(
		"LMS Program",
		{"published": 1},
		["name", "title", "course_count", "member_count"],
	)

	# Remove already enrolled programs from published list
	enrolled_names = [p.name for p in enrolled_programs]
	published_programs = [p for p in published_programs if p.name not in enrolled_names]

	return {
		"enrolled": enrolled_programs,
		"published": published_programs,
	}


@frappe.whitelist()
def patched_enroll_in_program(program):
	"""
	Patched version that blocks self-enrollment for students.

	Students cannot self-enroll into programs. Enrollment is managed
	by administrators through Education module's Program Enrollment.
	Moderators and instructors can still enroll.
	"""
	# Check if user is a student (has LMS Student role but not moderator/instructor)
	user_roles = frappe.get_roles(frappe.session.user)
	is_student = "LMS Student" in user_roles
	is_moderator = "Moderator" in user_roles
	is_instructor = "Course Creator" in user_roles or "Instructor" in user_roles
	is_admin = "System Manager" in user_roles or "Administrator" in user_roles

	if is_student and not (is_moderator or is_instructor or is_admin):
		frappe.msgprint(
			frappe._("Please contact your administrator for help enrolling, or apply if it's an open intake."),
			title=frappe._("Enrollment Not Available"),
			indicator="orange"
		)
		return

	# For non-students (moderators, instructors, admins), allow enrollment
	import lms.lms.utils as lms_utils
	return lms_utils._original_enroll_in_program(program)


def apply_lms_patches():
	"""Apply monkey patches to LMS module."""
	try:
		import lms.lms.utils as lms_utils

		# Store original functions for reference
		lms_utils._original_get_lesson_icon = lms_utils.get_lesson_icon
		lms_utils._original_get_lesson_details = lms_utils.get_lesson_details
		lms_utils._original_get_programs = lms_utils.get_programs
		lms_utils._original_enroll_in_program = lms_utils.enroll_in_program

		# Apply patches
		lms_utils.get_lesson_icon = patched_get_lesson_icon
		lms_utils.get_lesson_details = patched_get_lesson_details
		lms_utils.get_programs = patched_get_programs
		lms_utils.enroll_in_program = patched_enroll_in_program  # Block self-enrollment

	except ImportError:
		# LMS not installed, skip patching
		pass

	try:
		from lms.lms.doctype.course_lesson.course_lesson import CourseLesson

		# Store original method
		CourseLesson._original_save_lesson_details_in_quiz = CourseLesson.save_lesson_details_in_quiz

		# Apply patch
		CourseLesson.save_lesson_details_in_quiz = patched_save_lesson_details_in_quiz

	except ImportError:
		# LMS not installed, skip patching
		pass
