import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_sync_enabled,
	log_sync_error,
	get_lms_course_for_education_course,
)
from education_custom.lms_sync.content_sync import sync_content_to_chapter


def sync_topic(doc, method=None):
	"""Sync Topic to LMS Course Chapter on creation"""
	if not is_sync_enabled(doc):
		return

	try:
		# Find which courses this topic belongs to via Course Topic
		courses = get_courses_for_topic(doc.name)
		if not courses:
			return

		for course_name in courses:
			lms_course = get_lms_course_for_education_course(course_name)
			if not lms_course:
				continue

			chapter = create_chapter_from_topic(doc, lms_course)
			if chapter:
				frappe.db.set_value("Topic", doc.name, "lms_chapter", chapter, update_modified=False)
				# Sync all topic content as lessons
				sync_topic_content(doc, chapter)

	except Exception as e:
		log_sync_error(doc, e, "sync_topic")


def update_topic(doc, method=None):
	"""Update LMS Course Chapter when Topic is updated"""
	if not is_sync_enabled(doc):
		return

	try:
		if doc.lms_chapter and frappe.db.exists("Course Chapter", doc.lms_chapter):
			update_chapter_from_topic(doc)
			# Re-sync content
			sync_topic_content(doc, doc.lms_chapter)
		else:
			sync_topic(doc, method)

	except Exception as e:
		log_sync_error(doc, e, "update_topic")


def delete_topic(doc, method=None):
	"""Delete LMS Course Chapter when Topic is deleted"""
	try:
		if doc.lms_chapter and frappe.db.exists("Course Chapter", doc.lms_chapter):
			chapter = frappe.get_doc("Course Chapter", doc.lms_chapter)

			# Delete all lessons in the chapter first
			for lesson_ref in chapter.lessons:
				if frappe.db.exists("Course Lesson", lesson_ref.lesson):
					frappe.delete_doc("Course Lesson", lesson_ref.lesson, force=True)

			# Remove chapter from course's chapters table
			remove_chapter_from_course(chapter)

			# Delete the chapter
			frappe.delete_doc("Course Chapter", doc.lms_chapter, force=True)

	except Exception as e:
		log_sync_error(doc, e, "delete_topic")


def get_courses_for_topic(topic_name):
	"""Get Course names that contain this topic"""
	return frappe.db.get_all(
		"Course Topic",
		filters={"topic": topic_name},
		pluck="parent"
	)


def create_chapter_from_topic(topic_doc, lms_course):
	"""Create a Course Chapter from a Topic, or link to existing one"""
	# First check if a chapter already exists with this education_topic link
	existing = frappe.db.get_value("Course Chapter", {"education_topic": topic_doc.name}, "name")
	if existing:
		# Update the existing one and return
		chapter = frappe.get_doc("Course Chapter", existing)
		chapter.title = topic_doc.topic_name
		chapter.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		chapter._syncing_from_education = True
		chapter.save(ignore_permissions=True)
		return existing

	# Check if a chapter with the same title exists in this course
	existing_by_title = frappe.db.get_value("Course Chapter",
		{"title": topic_doc.topic_name, "course": lms_course}, "name")
	if existing_by_title:
		# Link it to this topic and update
		chapter = frappe.get_doc("Course Chapter", existing_by_title)
		chapter.education_topic = topic_doc.name
		chapter.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		chapter._syncing_from_education = True
		chapter.save(ignore_permissions=True)
		return existing_by_title

	chapter = frappe.get_doc({
		"doctype": "Course Chapter",
		"title": topic_doc.topic_name,
		"course": lms_course,
		"education_topic": topic_doc.name,
		"synced_from_education": 1,
	})
	# Set flag to prevent reverse sync loop
	chapter._syncing_from_education = True
	chapter.insert(ignore_permissions=True)

	# Add chapter to course's chapters child table - reload to get latest version
	lms_course_doc = frappe.get_doc("LMS Course", lms_course)
	# Check if chapter already in list
	existing_chapters = [c.chapter for c in lms_course_doc.chapters]
	if chapter.name not in existing_chapters:
		lms_course_doc.append("chapters", {"chapter": chapter.name})
		lms_course_doc.save(ignore_permissions=True)

	return chapter.name


def update_chapter_from_topic(topic_doc):
	"""Update Course Chapter from Topic"""
	# Skip if this update is coming from LMS reverse sync
	if getattr(topic_doc, "_syncing_from_lms", False):
		return

	chapter = frappe.get_doc("Course Chapter", topic_doc.lms_chapter)
	chapter.title = topic_doc.topic_name

	# Set flag to prevent reverse sync loop
	chapter._syncing_from_education = True
	chapter.save(ignore_permissions=True)


def remove_chapter_from_course(chapter_doc):
	"""Remove chapter from course's chapters table"""
	if not chapter_doc.course:
		return

	course = frappe.get_doc("LMS Course", chapter_doc.course)
	course.chapters = [c for c in course.chapters if c.chapter != chapter_doc.name]
	course.save(ignore_permissions=True)


def sync_topic_content(topic_doc, chapter_name):
	"""Sync all topic content (Articles, Videos) to chapter as lessons - handles add and remove"""
	topic = frappe.get_doc("Topic", topic_doc.name)

	# Get current education content in topic (excluding Quiz)
	education_content = []
	for content in topic.topic_content:
		if content.content_type in ("Article", "Video"):
			education_content.append((content.content_type, content.content))

	# Get lessons that should exist
	target_lessons = []
	for content_type, content_name in education_content:
		# Skip if content doesn't exist
		if not frappe.db.exists(content_type, content_name):
			frappe.log_error(f"Skipping missing {content_type}: {content_name}", "LMS Sync Warning")
			continue

		try:
			content_doc = frappe.get_doc(content_type, content_name)

			if content_doc.lms_lesson and frappe.db.exists("Course Lesson", content_doc.lms_lesson):
				target_lessons.append(content_doc.lms_lesson)
			else:
				# Sync content to create lesson
				lesson = sync_content_to_chapter(content_type, content_name, chapter_name)
				if lesson:
					frappe.db.set_value(content_type, content_name, "lms_lesson", lesson, update_modified=False)
					target_lessons.append(lesson)
		except Exception as e:
			frappe.log_error(f"Error syncing {content_type} {content_name}: {str(e)}", "LMS Sync Warning")
			continue

	# Reload chapter to get latest version after content syncs
	chapter = frappe.get_doc("Course Chapter", chapter_name)

	# Get current lessons in chapter
	current_lessons = [l.lesson for l in chapter.lessons]

	# Track if we need to save
	needs_save = False

	# Add new lessons
	for lesson in target_lessons:
		if lesson not in current_lessons:
			chapter.append("lessons", {"lesson": lesson})
			needs_save = True

	# Remove lessons that are no longer in topic content
	# Only remove if they were synced from education
	lessons_to_remove = []
	for lesson_ref in chapter.lessons:
		if lesson_ref.lesson not in target_lessons and is_synced_lesson(lesson_ref.lesson):
			lessons_to_remove.append(lesson_ref.lesson)

	if lessons_to_remove:
		# Remove lessons from chapter
		chapter.lessons = [
			l for l in chapter.lessons
			if l.lesson not in lessons_to_remove
		]
		needs_save = True

	if needs_save:
		chapter.save(ignore_permissions=True)

	# Delete the removed lessons
	for lesson_name in lessons_to_remove:
		delete_lesson(lesson_name)


def is_synced_lesson(lesson_name):
	"""Check if Course Lesson was synced from Education"""
	return frappe.db.get_value("Course Lesson", lesson_name, "synced_from_education")


def delete_lesson(lesson_name):
	"""Delete a lesson and clear the link in Article/Video"""
	if not frappe.db.exists("Course Lesson", lesson_name):
		return

	lesson = frappe.get_doc("Course Lesson", lesson_name)

	# Clear link in Article/Video
	if lesson.education_content_type and lesson.education_content:
		frappe.db.set_value(
			lesson.education_content_type,
			lesson.education_content,
			"lms_lesson",
			None,
			update_modified=False
		)

	frappe.delete_doc("Course Lesson", lesson_name, force=True)


def sync_topic_to_course(topic_name, lms_course):
	"""
	Helper to sync a topic to a specific course
	Used when syncing courses and their topics together
	"""
	topic = frappe.get_doc("Topic", topic_name)
	if not is_sync_enabled(topic):
		return None

	# Check if topic already has a chapter linked
	if topic.lms_chapter and frappe.db.exists("Course Chapter", topic.lms_chapter):
		# Just sync the content
		sync_topic_content(topic, topic.lms_chapter)
		return topic.lms_chapter

	chapter = create_chapter_from_topic(topic, lms_course)
	if chapter:
		frappe.db.set_value("Topic", topic_name, "lms_chapter", chapter, update_modified=False)
		sync_topic_content(topic, chapter)
		return chapter

	return None
