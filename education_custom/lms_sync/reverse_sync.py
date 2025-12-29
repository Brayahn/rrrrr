"""
Reverse Sync: LMS to Education
Syncs changes from LMS Course Lessons back to Education Articles/Videos
"""
import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_lms_installed,
	markdown_to_html,
	log_sync_error,
)


def is_reverse_sync_enabled():
	"""Check if reverse sync is enabled"""
	if not is_lms_installed():
		return False
	# Could add a setting to enable/disable reverse sync
	return True


def sync_lesson_to_education(doc, method=None):
	"""
	Sync Course Lesson changes back to Education Article/Video
	Called on Course Lesson update
	"""
	if not is_reverse_sync_enabled():
		return

	# Skip if this lesson was just synced from education (prevent loop)
	if getattr(doc, "_syncing_from_education", False):
		return

	# Skip if lesson is not linked to education content
	if not doc.education_content_type or not doc.education_content:
		return

	try:
		if doc.education_content_type == "Article":
			sync_lesson_to_article(doc)
		elif doc.education_content_type == "Video":
			sync_lesson_to_video(doc)
	except Exception as e:
		log_sync_error(doc, e, "reverse_sync_lesson")


def sync_lesson_to_article(lesson_doc):
	"""Sync Course Lesson back to Article"""
	if not frappe.db.exists("Article", lesson_doc.education_content):
		return

	article = frappe.get_doc("Article", lesson_doc.education_content)

	# Check if there are actual changes
	new_content = markdown_to_html(lesson_doc.body) if lesson_doc.body else ""
	title_changed = article.title != lesson_doc.title
	content_changed = normalize_html(article.content or "") != normalize_html(new_content)

	if not title_changed and not content_changed:
		return

	# Update article
	article.title = lesson_doc.title

	if lesson_doc.body:
		article.content = new_content

	# Set flag to prevent sync loop
	article._syncing_from_lms = True
	article.flags.ignore_validate_update_after_submit = True
	article.save(ignore_permissions=True)

	frappe.msgprint(
		_("Article '{0}' updated from LMS").format(article.title),
		indicator="blue",
		alert=True
	)


def sync_lesson_to_video(lesson_doc):
	"""Sync Course Lesson back to Video"""
	if not frappe.db.exists("Video", lesson_doc.education_content):
		return

	video = frappe.get_doc("Video", lesson_doc.education_content)

	# Check if there are actual changes
	title_changed = video.title != lesson_doc.title
	url_changed = False

	# Check if YouTube URL changed
	if lesson_doc.youtube and video.url != lesson_doc.youtube:
		url_changed = True
		new_url = lesson_doc.youtube
	else:
		new_url = video.url

	# Check description change (from lesson body minus video link)
	new_description = ""
	if lesson_doc.body:
		# Remove the video link line if present
		body = lesson_doc.body
		body = body.replace(f"[Video: {video.title}]({video.url})", "").strip()
		body = body.replace(f"[Video: {lesson_doc.title}]({video.url})", "").strip()
		if body:
			new_description = markdown_to_html(body)

	description_changed = normalize_html(video.description or "") != normalize_html(new_description)

	if not title_changed and not url_changed and not description_changed:
		return

	# Update video
	video.title = lesson_doc.title

	if url_changed:
		video.url = new_url

	if new_description:
		video.description = new_description

	# Set flag to prevent sync loop
	video._syncing_from_lms = True
	video.flags.ignore_validate_update_after_submit = True
	video.save(ignore_permissions=True)

	frappe.msgprint(
		_("Video '{0}' updated from LMS").format(video.title),
		indicator="blue",
		alert=True
	)


def sync_chapter_to_topic(doc, method=None):
	"""
	Sync Course Chapter changes back to Education Topic
	Called on Course Chapter update
	"""
	if not is_reverse_sync_enabled():
		return

	# Skip if this chapter was just synced from education (prevent loop)
	if getattr(doc, "_syncing_from_education", False):
		return

	# Skip if chapter is not linked to education topic
	if not doc.education_topic:
		return

	try:
		if not frappe.db.exists("Topic", doc.education_topic):
			return

		topic = frappe.get_doc("Topic", doc.education_topic)

		# Check if title changed
		if topic.topic_name == doc.title:
			return

		# Update topic
		topic.topic_name = doc.title

		# Set flag to prevent sync loop
		topic._syncing_from_lms = True
		topic.flags.ignore_validate_update_after_submit = True
		topic.save(ignore_permissions=True)

		frappe.msgprint(
			_("Topic '{0}' updated from LMS").format(topic.topic_name),
			indicator="blue",
			alert=True
		)

	except Exception as e:
		log_sync_error(doc, e, "reverse_sync_chapter")


def sync_course_to_education(doc, method=None):
	"""
	Sync LMS Course changes back to Education Course
	Called on LMS Course update
	"""
	if not is_reverse_sync_enabled():
		return

	# Skip if this course was just synced from education (prevent loop)
	if getattr(doc, "_syncing_from_education", False):
		return

	# Skip if course is not linked to education course
	if not doc.education_course:
		return

	try:
		if not frappe.db.exists("Course", doc.education_course):
			return

		course = frappe.get_doc("Course", doc.education_course)

		# Check if there are actual changes
		title_changed = course.course_name != doc.title
		description_changed = False

		if doc.description:
			new_desc = markdown_to_html(doc.description) if not doc.description.startswith('<') else doc.description
			description_changed = normalize_html(course.description or "") != normalize_html(new_desc)

		if not title_changed and not description_changed:
			return

		# Update course
		if title_changed:
			course.course_name = doc.title

		if description_changed and doc.description:
			course.description = new_desc if not doc.description.startswith('<') else doc.description

		# Set flag to prevent sync loop
		course._syncing_from_lms = True
		course.flags.ignore_validate_update_after_submit = True
		course.save(ignore_permissions=True)

		frappe.msgprint(
			_("Course '{0}' updated from LMS").format(course.course_name),
			indicator="blue",
			alert=True
		)

	except Exception as e:
		log_sync_error(doc, e, "reverse_sync_course")


def sync_program_to_education(doc, method=None):
	"""
	Sync LMS Program changes back to Education Program
	Called on LMS Program update
	"""
	if not is_reverse_sync_enabled():
		return

	# Skip if this program was just synced from education (prevent loop)
	if getattr(doc, "_syncing_from_education", False):
		return

	# Skip if program is not linked to education program
	if not doc.education_program:
		return

	try:
		if not frappe.db.exists("Program", doc.education_program):
			return

		program = frappe.get_doc("Program", doc.education_program)

		# Check if title changed
		if program.program_name == doc.title:
			return

		# Update program
		program.program_name = doc.title

		# Set flag to prevent sync loop
		program._syncing_from_lms = True
		program.flags.ignore_validate_update_after_submit = True
		program.save(ignore_permissions=True)

		frappe.msgprint(
			_("Program '{0}' updated from LMS").format(program.program_name),
			indicator="blue",
			alert=True
		)

	except Exception as e:
		log_sync_error(doc, e, "reverse_sync_program")


def normalize_html(html):
	"""Normalize HTML for comparison by removing extra whitespace"""
	if not html:
		return ""
	import re
	# Remove extra whitespace
	html = re.sub(r'\s+', ' ', html)
	# Remove whitespace around tags
	html = re.sub(r'>\s+<', '><', html)
	return html.strip().lower()
