import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_sync_enabled,
	log_sync_error,
	has_lms_enrollments,
)
from education_custom.lms_sync.topic_sync import sync_topic_to_course


def sync_course(doc, method=None):
	"""Sync Education Course to LMS Course on creation"""
	if not is_sync_enabled(doc):
		return

	try:
		lms_course = create_lms_course(doc)
		if lms_course:
			frappe.db.set_value("Course", doc.name, "lms_course", lms_course, update_modified=False)
			# Sync all topics as chapters
			sync_course_topics(doc, lms_course)

	except Exception as e:
		log_sync_error(doc, e, "sync_course")


def update_course(doc, method=None):
	"""Update LMS Course when Education Course is updated"""
	if not is_sync_enabled(doc):
		return

	try:
		if doc.lms_course and frappe.db.exists("LMS Course", doc.lms_course):
			update_lms_course(doc)
			# Re-sync topics
			sync_course_topics(doc, doc.lms_course)
		else:
			sync_course(doc, method)

	except Exception as e:
		log_sync_error(doc, e, "update_course")


def delete_course(doc, method=None):
	"""Delete LMS Course when Education Course is deleted"""
	try:
		if doc.lms_course and frappe.db.exists("LMS Course", doc.lms_course):
			# Check for enrollments
			if has_lms_enrollments(doc.lms_course):
				frappe.throw(
					_("Cannot delete Course. The linked LMS Course has active enrollments. "
					  "Please remove LMS enrollments first or unlink the course."),
					title=_("LMS Course Has Enrollments")
				)

			lms_course = frappe.get_doc("LMS Course", doc.lms_course)

			# Delete all chapters and their lessons first
			for chapter_ref in lms_course.chapters:
				if frappe.db.exists("Course Chapter", chapter_ref.chapter):
					chapter = frappe.get_doc("Course Chapter", chapter_ref.chapter)
					# Delete lessons
					for lesson_ref in chapter.lessons:
						if frappe.db.exists("Course Lesson", lesson_ref.lesson):
							frappe.delete_doc("Course Lesson", lesson_ref.lesson, force=True)
					frappe.delete_doc("Course Chapter", chapter_ref.chapter, force=True)

			# Delete the LMS course
			frappe.delete_doc("LMS Course", doc.lms_course, force=True)

	except frappe.ValidationError:
		raise
	except Exception as e:
		log_sync_error(doc, e, "delete_course")


def create_lms_course(course_doc):
	"""Create an LMS Course from Education Course, or link to existing one"""
	# First check if an LMS Course already exists with this education_course link
	existing = frappe.db.get_value("LMS Course", {"education_course": course_doc.name}, "name")
	if existing:
		# Update the existing one and return
		lms_course = frappe.get_doc("LMS Course", existing)
		lms_course.title = course_doc.course_name
		lms_course.description = course_doc.description or f"Course: {course_doc.course_name}"
		lms_course.short_introduction = lms_course.description[:200]
		lms_course.synced_from_education = 1
		if course_doc.hero_image:
			lms_course.image = course_doc.hero_image
		# Set flag to prevent reverse sync loop
		lms_course._syncing_from_education = True
		lms_course.save(ignore_permissions=True)
		return existing

	# Check if an LMS Course with the same title exists
	existing_by_title = frappe.db.get_value("LMS Course", {"title": course_doc.course_name}, "name")
	if existing_by_title:
		# Link it to this education course and update
		lms_course = frappe.get_doc("LMS Course", existing_by_title)
		lms_course.education_course = course_doc.name
		lms_course.synced_from_education = 1
		lms_course.description = course_doc.description or lms_course.description or f"Course: {course_doc.course_name}"
		lms_course.short_introduction = lms_course.description[:200]
		if course_doc.hero_image:
			lms_course.image = course_doc.hero_image
		# Set flag to prevent reverse sync loop
		lms_course._syncing_from_education = True
		lms_course.save(ignore_permissions=True)
		return existing_by_title

	# Get description or create default
	description = course_doc.description or f"Course: {course_doc.course_name}"
	short_intro = description[:200] if len(description) > 200 else description

	# Use document owner as instructor
	instructor = course_doc.owner

	lms_course = frappe.get_doc({
		"doctype": "LMS Course",
		"name": course_doc.name,  # Use education course name directly
		"title": course_doc.course_name,
		"description": description,
		"short_introduction": short_intro,
		"published": 1,  # Auto-publish as per user preference
		"instructors": [{"instructor": instructor}],
		"education_course": course_doc.name,
		"synced_from_education": 1,
	})

	# Copy image if exists
	if course_doc.hero_image:
		lms_course.image = course_doc.hero_image

	# Set flag to prevent reverse sync loop
	lms_course._syncing_from_education = True
	lms_course.insert(ignore_permissions=True)

	return lms_course.name


def update_lms_course(course_doc):
	"""Update LMS Course from Education Course"""
	# Skip if this update is coming from LMS reverse sync
	if getattr(course_doc, "_syncing_from_lms", False):
		return

	lms_course = frappe.get_doc("LMS Course", course_doc.lms_course)

	lms_course.title = course_doc.course_name
	lms_course.description = course_doc.description or f"Course: {course_doc.course_name}"
	lms_course.short_introduction = lms_course.description[:200]

	if course_doc.hero_image:
		lms_course.image = course_doc.hero_image

	# Set flag to prevent reverse sync loop
	lms_course._syncing_from_education = True
	lms_course.save(ignore_permissions=True)


def sync_course_topics(course_doc, lms_course):
	"""Sync all topics of a course to LMS as chapters - handles add and remove"""
	course = frappe.get_doc("Course", course_doc.name)

	# Get current education topics in course
	education_topics = [t.topic for t in course.topics]

	# Get chapters that should exist (synced from education topics)
	target_chapters = []
	for topic_name in education_topics:
		# Skip if topic doesn't exist
		if not frappe.db.exists("Topic", topic_name):
			frappe.log_error(f"Skipping missing Topic: {topic_name}", "LMS Sync Warning")
			continue

		try:
			topic = frappe.get_doc("Topic", topic_name)

			if topic.lms_chapter and frappe.db.exists("Course Chapter", topic.lms_chapter):
				target_chapters.append(topic.lms_chapter)
			else:
				# Sync topic to create chapter
				chapter = sync_topic_to_course(topic_name, lms_course)
				if chapter:
					target_chapters.append(chapter)
		except Exception as e:
			frappe.log_error(f"Error syncing Topic {topic_name}: {str(e)}", "LMS Sync Warning")
			continue

	# Reload LMS course to get latest version after topic syncs may have modified it
	lms_course_doc = frappe.get_doc("LMS Course", lms_course)

	# Get current chapters in LMS course
	current_chapters = [c.chapter for c in lms_course_doc.chapters]

	# Track if we need to save
	needs_save = False

	# Add new chapters
	for chapter in target_chapters:
		if chapter not in current_chapters:
			lms_course_doc.append("chapters", {"chapter": chapter})
			needs_save = True

	# Remove chapters that are no longer in education course
	# Only remove if they were synced from education
	chapters_to_remove = []
	for chapter_ref in lms_course_doc.chapters:
		if chapter_ref.chapter not in target_chapters and is_synced_chapter(chapter_ref.chapter):
			chapters_to_remove.append(chapter_ref.chapter)

	if chapters_to_remove:
		# Remove chapters from course
		lms_course_doc.chapters = [
			c for c in lms_course_doc.chapters
			if c.chapter not in chapters_to_remove
		]
		needs_save = True

	if needs_save:
		lms_course_doc.save(ignore_permissions=True)

	# Delete the removed chapters and their lessons
	for chapter_name in chapters_to_remove:
		delete_chapter_and_lessons(chapter_name)


def is_synced_chapter(chapter_name):
	"""Check if Course Chapter was synced from Education"""
	return frappe.db.get_value("Course Chapter", chapter_name, "synced_from_education")


def delete_chapter_and_lessons(chapter_name):
	"""Delete a chapter and all its lessons"""
	if not frappe.db.exists("Course Chapter", chapter_name):
		return

	chapter = frappe.get_doc("Course Chapter", chapter_name)

	# Clear the link in Topic
	if chapter.education_topic:
		frappe.db.set_value("Topic", chapter.education_topic, "lms_chapter", None, update_modified=False)

	# Delete lessons
	for lesson_ref in chapter.lessons:
		if frappe.db.exists("Course Lesson", lesson_ref.lesson):
			lesson = frappe.get_doc("Course Lesson", lesson_ref.lesson)
			# Clear link in Article/Video
			if lesson.education_content_type and lesson.education_content:
				frappe.db.set_value(
					lesson.education_content_type,
					lesson.education_content,
					"lms_lesson",
					None,
					update_modified=False
				)
			frappe.delete_doc("Course Lesson", lesson_ref.lesson, force=True)

	frappe.delete_doc("Course Chapter", chapter_name, force=True)


def sync_course_to_program(course_name, lms_program):
	"""
	Helper to sync a course to an LMS program
	Used when syncing programs and their courses together
	Returns the LMS Course name
	"""
	course = frappe.get_doc("Course", course_name)
	if not is_sync_enabled(course):
		return None

	# Check if LMS course already exists and is valid
	if course.lms_course and frappe.db.exists("LMS Course", course.lms_course):
		# Sync topics to ensure they're up to date
		sync_course_topics(course, course.lms_course)
		return course.lms_course

	# Create or link LMS course
	lms_course = create_lms_course(course)
	if lms_course:
		frappe.db.set_value("Course", course_name, "lms_course", lms_course, update_modified=False)
		sync_course_topics(course, lms_course)
		return lms_course

	return None
