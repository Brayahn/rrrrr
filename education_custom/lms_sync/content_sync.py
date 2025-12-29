import frappe
from frappe import _

from education_custom.lms_sync.utils import (
	is_sync_enabled,
	html_to_markdown,
	get_youtube_id,
	is_youtube_url,
	log_sync_error,
	get_chapter_for_topic,
)


def sync_article(doc, method=None):
	"""Sync Article to LMS Course Lesson on creation"""
	if not is_sync_enabled(doc):
		return

	try:
		# Find the Topic(s) this article belongs to via Topic Content
		topics = get_topics_for_content("Article", doc.name)
		if not topics:
			return

		for topic_name in topics:
			chapter = get_chapter_for_topic(topic_name)
			if not chapter:
				continue

			lesson = create_lesson_from_article(doc, chapter)
			if lesson:
				# Store link back to lesson
				frappe.db.set_value("Article", doc.name, "lms_lesson", lesson, update_modified=False)

	except Exception as e:
		log_sync_error(doc, e, "sync_article")


def update_article(doc, method=None):
	"""Update LMS Course Lesson when Article is updated"""
	if not is_sync_enabled(doc):
		return

	try:
		if doc.lms_lesson and frappe.db.exists("Course Lesson", doc.lms_lesson):
			update_lesson_from_article(doc)
		else:
			# Lesson doesn't exist, try to create
			sync_article(doc, method)

	except Exception as e:
		log_sync_error(doc, e, "update_article")


def delete_article(doc, method=None):
	"""Delete LMS Course Lesson when Article is deleted"""
	try:
		if doc.lms_lesson and frappe.db.exists("Course Lesson", doc.lms_lesson):
			lesson = frappe.get_doc("Course Lesson", doc.lms_lesson)
			remove_lesson_from_chapter(lesson)
			frappe.delete_doc("Course Lesson", doc.lms_lesson, force=True)

	except Exception as e:
		log_sync_error(doc, e, "delete_article")


def sync_video(doc, method=None):
	"""Sync Video to LMS Course Lesson on creation"""
	if not is_sync_enabled(doc):
		return

	try:
		# Find the Topic(s) this video belongs to via Topic Content
		topics = get_topics_for_content("Video", doc.name)
		if not topics:
			return

		for topic_name in topics:
			chapter = get_chapter_for_topic(topic_name)
			if not chapter:
				continue

			lesson = create_lesson_from_video(doc, chapter)
			if lesson:
				frappe.db.set_value("Video", doc.name, "lms_lesson", lesson, update_modified=False)

	except Exception as e:
		log_sync_error(doc, e, "sync_video")


def update_video(doc, method=None):
	"""Update LMS Course Lesson when Video is updated"""
	if not is_sync_enabled(doc):
		return

	try:
		if doc.lms_lesson and frappe.db.exists("Course Lesson", doc.lms_lesson):
			update_lesson_from_video(doc)
		else:
			sync_video(doc, method)

	except Exception as e:
		log_sync_error(doc, e, "update_video")


def delete_video(doc, method=None):
	"""Delete LMS Course Lesson when Video is deleted"""
	try:
		if doc.lms_lesson and frappe.db.exists("Course Lesson", doc.lms_lesson):
			lesson = frappe.get_doc("Course Lesson", doc.lms_lesson)
			remove_lesson_from_chapter(lesson)
			frappe.delete_doc("Course Lesson", doc.lms_lesson, force=True)

	except Exception as e:
		log_sync_error(doc, e, "delete_video")


def get_topics_for_content(content_type, content_name):
	"""Get Topic names that contain this content"""
	return frappe.db.get_all(
		"Topic Content",
		filters={"content_type": content_type, "content": content_name},
		pluck="parent"
	)


def create_lesson_from_article(article_doc, chapter_name):
	"""Create a Course Lesson from an Article, or link to existing one"""
	# First check if a lesson already exists with this education_content link
	existing = frappe.db.get_value("Course Lesson", {
		"education_content_type": "Article",
		"education_content": article_doc.name
	}, "name")
	if existing:
		# Update the existing one and return
		lesson = frappe.get_doc("Course Lesson", existing)
		lesson.title = article_doc.title
		lesson.body = html_to_markdown(article_doc.content) if article_doc.content else ""
		lesson.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lesson._syncing_from_education = True
		lesson.save(ignore_permissions=True)
		return existing

	# Check if a lesson with the same title exists in this chapter
	existing_by_title = frappe.db.get_value("Course Lesson",
		{"title": article_doc.title, "chapter": chapter_name}, "name")
	if existing_by_title:
		# Link it to this article and update
		lesson = frappe.get_doc("Course Lesson", existing_by_title)
		lesson.education_content_type = "Article"
		lesson.education_content = article_doc.name
		lesson.body = html_to_markdown(article_doc.content) if article_doc.content else ""
		lesson.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lesson._syncing_from_education = True
		lesson.save(ignore_permissions=True)
		return existing_by_title

	# Convert HTML content to markdown
	body = html_to_markdown(article_doc.content) if article_doc.content else ""

	lesson = frappe.get_doc({
		"doctype": "Course Lesson",
		"title": article_doc.title,
		"chapter": chapter_name,
		"body": body,
		"education_content_type": "Article",
		"education_content": article_doc.name,
		"synced_from_education": 1,
	})
	# Set flag to prevent reverse sync loop
	lesson._syncing_from_education = True
	lesson.insert(ignore_permissions=True)

	# Add lesson to chapter's lessons child table - reload to get latest
	chapter = frappe.get_doc("Course Chapter", chapter_name)
	existing_lessons = [l.lesson for l in chapter.lessons]
	if lesson.name not in existing_lessons:
		chapter.append("lessons", {"lesson": lesson.name})
		chapter.save(ignore_permissions=True)

	return lesson.name


def update_lesson_from_article(article_doc):
	"""Update Course Lesson from Article"""
	# Skip if this update is coming from LMS reverse sync
	if getattr(article_doc, "_syncing_from_lms", False):
		return

	lesson = frappe.get_doc("Course Lesson", article_doc.lms_lesson)

	lesson.title = article_doc.title
	lesson.body = html_to_markdown(article_doc.content) if article_doc.content else ""

	# Set flag to prevent reverse sync loop
	lesson._syncing_from_education = True
	lesson.save(ignore_permissions=True)


def create_lesson_from_video(video_doc, chapter_name):
	"""Create a Course Lesson from a Video, or link to existing one"""
	# First check if a lesson already exists with this education_content link
	existing = frappe.db.get_value("Course Lesson", {
		"education_content_type": "Video",
		"education_content": video_doc.name
	}, "name")
	if existing:
		# Update the existing one and return
		lesson = frappe.get_doc("Course Lesson", existing)
		lesson.title = video_doc.title
		if is_youtube_url(video_doc.url):
			lesson.youtube = video_doc.url
			lesson.body = ""
		else:
			lesson.youtube = ""
			lesson.body = f"[Video: {video_doc.title}]({video_doc.url})"
		if video_doc.description:
			desc = html_to_markdown(video_doc.description)
			if lesson.body:
				lesson.body = f"{lesson.body}\n\n{desc}"
			else:
				lesson.body = desc
		lesson.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lesson._syncing_from_education = True
		lesson.save(ignore_permissions=True)
		return existing

	# Check if a lesson with the same title exists in this chapter
	existing_by_title = frappe.db.get_value("Course Lesson",
		{"title": video_doc.title, "chapter": chapter_name}, "name")
	if existing_by_title:
		# Link it to this video and update
		lesson = frappe.get_doc("Course Lesson", existing_by_title)
		lesson.education_content_type = "Video"
		lesson.education_content = video_doc.name
		if is_youtube_url(video_doc.url):
			lesson.youtube = video_doc.url
			lesson.body = ""
		else:
			lesson.youtube = ""
			lesson.body = f"[Video: {video_doc.title}]({video_doc.url})"
		if video_doc.description:
			desc = html_to_markdown(video_doc.description)
			if lesson.body:
				lesson.body = f"{lesson.body}\n\n{desc}"
			else:
				lesson.body = desc
		lesson.synced_from_education = 1
		# Set flag to prevent reverse sync loop
		lesson._syncing_from_education = True
		lesson.save(ignore_permissions=True)
		return existing_by_title

	# Handle YouTube videos specially
	body = ""
	youtube_url = ""

	if is_youtube_url(video_doc.url):
		youtube_url = video_doc.url
	else:
		# For non-YouTube videos, embed in markdown
		body = f"[Video: {video_doc.title}]({video_doc.url})"

	# Add description if exists
	if video_doc.description:
		desc = html_to_markdown(video_doc.description)
		if body:
			body = f"{body}\n\n{desc}"
		else:
			body = desc

	lesson = frappe.get_doc({
		"doctype": "Course Lesson",
		"title": video_doc.title,
		"chapter": chapter_name,
		"body": body,
		"youtube": youtube_url,
		"education_content_type": "Video",
		"education_content": video_doc.name,
		"synced_from_education": 1,
	})
	# Set flag to prevent reverse sync loop
	lesson._syncing_from_education = True
	lesson.insert(ignore_permissions=True)

	# Add lesson to chapter - reload to get latest
	chapter = frappe.get_doc("Course Chapter", chapter_name)
	existing_lessons = [l.lesson for l in chapter.lessons]
	if lesson.name not in existing_lessons:
		chapter.append("lessons", {"lesson": lesson.name})
		chapter.save(ignore_permissions=True)

	return lesson.name


def update_lesson_from_video(video_doc):
	"""Update Course Lesson from Video"""
	# Skip if this update is coming from LMS reverse sync
	if getattr(video_doc, "_syncing_from_lms", False):
		return

	lesson = frappe.get_doc("Course Lesson", video_doc.lms_lesson)

	lesson.title = video_doc.title

	if is_youtube_url(video_doc.url):
		lesson.youtube = video_doc.url
		lesson.body = ""
	else:
		lesson.youtube = ""
		lesson.body = f"[Video: {video_doc.title}]({video_doc.url})"

	if video_doc.description:
		desc = html_to_markdown(video_doc.description)
		if lesson.body:
			lesson.body = f"{lesson.body}\n\n{desc}"
		else:
			lesson.body = desc

	# Set flag to prevent reverse sync loop
	lesson._syncing_from_education = True
	lesson.save(ignore_permissions=True)


def remove_lesson_from_chapter(lesson_doc):
	"""Remove lesson from chapter's lessons table"""
	if not lesson_doc.chapter:
		return

	chapter = frappe.get_doc("Course Chapter", lesson_doc.chapter)
	chapter.lessons = [l for l in chapter.lessons if l.lesson != lesson_doc.name]
	chapter.save(ignore_permissions=True)


def sync_content_to_chapter(content_type, content_name, chapter_name):
	"""
	Helper to sync content to a specific chapter
	Used when syncing topics and their content together
	"""
	try:
		if content_type == "Article":
			if not frappe.db.exists("Article", content_name):
				return None
			article = frappe.get_doc("Article", content_name)
			if not is_sync_enabled(article):
				return None
			# Check if already has a lesson linked
			if article.lms_lesson and frappe.db.exists("Course Lesson", article.lms_lesson):
				return article.lms_lesson
			return create_lesson_from_article(article, chapter_name)
		elif content_type == "Video":
			if not frappe.db.exists("Video", content_name):
				return None
			video = frappe.get_doc("Video", content_name)
			if not is_sync_enabled(video):
				return None
			# Check if already has a lesson linked
			if video.lms_lesson and frappe.db.exists("Course Lesson", video.lms_lesson):
				return video.lms_lesson
			return create_lesson_from_video(video, chapter_name)
	except Exception as e:
		frappe.log_error(f"Error syncing {content_type} {content_name}: {str(e)}", "LMS Sync Warning")
		return None

	return None
