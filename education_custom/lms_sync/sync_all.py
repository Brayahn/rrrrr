import frappe
from frappe import _

from education_custom.lms_sync.utils import is_lms_installed, is_sync_enabled


@frappe.whitelist()
def sync_all_to_lms():
	"""
	Sync all existing Education items to LMS.
	Call this once to create initial links, or to resync everything.
	"""
	if not is_lms_installed():
		frappe.throw(_("LMS app is not installed"))

	results = {
		"programs": 0,
		"courses": 0,
		"topics": 0,
		"articles": 0,
		"videos": 0,
		"errors": []
	}

	# Sync in order: Programs -> Courses -> Topics -> Content
	frappe.publish_realtime("lms_sync_progress", {"message": "Syncing Programs..."})
	results["programs"] = sync_all_programs(results["errors"])

	frappe.publish_realtime("lms_sync_progress", {"message": "Syncing Courses..."})
	results["courses"] = sync_all_courses(results["errors"])

	frappe.publish_realtime("lms_sync_progress", {"message": "Syncing Topics..."})
	results["topics"] = sync_all_topics(results["errors"])

	frappe.publish_realtime("lms_sync_progress", {"message": "Syncing Articles..."})
	results["articles"] = sync_all_articles(results["errors"])

	frappe.publish_realtime("lms_sync_progress", {"message": "Syncing Videos..."})
	results["videos"] = sync_all_videos(results["errors"])

	frappe.publish_realtime("lms_sync_progress", {"message": "Sync complete!"})

	return results


def sync_all_programs(errors):
	"""Sync all programs that don't have LMS link"""
	from education_custom.lms_sync.program_sync import create_lms_program, sync_program_courses

	count = 0
	programs = frappe.get_all(
		"Program",
		filters={"lms_program": ["is", "not set"]},
		pluck="name"
	)

	for program_name in programs:
		try:
			program = frappe.get_doc("Program", program_name)
			if not is_sync_enabled(program):
				continue

			lms_program = create_lms_program(program)
			if lms_program:
				frappe.db.set_value("Program", program_name, "lms_program", lms_program, update_modified=False)
				sync_program_courses(program, lms_program)
				count += 1
		except Exception as e:
			errors.append(f"Program {program_name}: {str(e)}")

	frappe.db.commit()
	return count


def sync_all_courses(errors):
	"""Sync all courses that don't have LMS link"""
	from education_custom.lms_sync.course_sync import create_lms_course, sync_course_topics

	count = 0
	courses = frappe.get_all(
		"Course",
		filters={"lms_course": ["is", "not set"]},
		pluck="name"
	)

	for course_name in courses:
		try:
			course = frappe.get_doc("Course", course_name)
			if not is_sync_enabled(course):
				continue

			lms_course = create_lms_course(course)
			if lms_course:
				frappe.db.set_value("Course", course_name, "lms_course", lms_course, update_modified=False)
				sync_course_topics(course, lms_course)
				count += 1
		except Exception as e:
			errors.append(f"Course {course_name}: {str(e)}")

	frappe.db.commit()
	return count


def sync_all_topics(errors):
	"""Sync all topics that don't have LMS link but belong to a synced course"""
	from education_custom.lms_sync.topic_sync import create_chapter_from_topic, sync_topic_content
	from education_custom.lms_sync.utils import get_lms_course_for_education_course

	count = 0
	# Get topics that are in courses
	topic_courses = frappe.db.sql("""
		SELECT ct.topic, ct.parent as course
		FROM `tabCourse Topic` ct
		JOIN `tabTopic` t ON t.name = ct.topic
		WHERE (t.lms_chapter IS NULL OR t.lms_chapter = '')
	""", as_dict=True)

	for row in topic_courses:
		try:
			topic = frappe.get_doc("Topic", row.topic)
			if not is_sync_enabled(topic):
				continue

			lms_course = get_lms_course_for_education_course(row.course)
			if not lms_course:
				continue

			chapter = create_chapter_from_topic(topic, lms_course)
			if chapter:
				frappe.db.set_value("Topic", row.topic, "lms_chapter", chapter, update_modified=False)
				sync_topic_content(topic, chapter)
				count += 1
		except Exception as e:
			errors.append(f"Topic {row.topic}: {str(e)}")

	frappe.db.commit()
	return count


def sync_all_articles(errors):
	"""Sync all articles that don't have LMS link but belong to a synced topic"""
	from education_custom.lms_sync.content_sync import create_lesson_from_article
	from education_custom.lms_sync.utils import get_chapter_for_topic

	count = 0
	# Get articles that are in topics
	article_topics = frappe.db.sql("""
		SELECT tc.content, tc.parent as topic
		FROM `tabTopic Content` tc
		JOIN `tabArticle` a ON a.name = tc.content
		WHERE tc.content_type = 'Article'
		AND (a.lms_lesson IS NULL OR a.lms_lesson = '')
	""", as_dict=True)

	for row in article_topics:
		try:
			article = frappe.get_doc("Article", row.content)
			if not is_sync_enabled(article):
				continue

			chapter = get_chapter_for_topic(row.topic)
			if not chapter:
				continue

			lesson = create_lesson_from_article(article, chapter)
			if lesson:
				frappe.db.set_value("Article", row.content, "lms_lesson", lesson, update_modified=False)
				count += 1
		except Exception as e:
			errors.append(f"Article {row.content}: {str(e)}")

	frappe.db.commit()
	return count


def sync_all_videos(errors):
	"""Sync all videos that don't have LMS link but belong to a synced topic"""
	from education_custom.lms_sync.content_sync import create_lesson_from_video
	from education_custom.lms_sync.utils import get_chapter_for_topic

	count = 0
	# Get videos that are in topics
	video_topics = frappe.db.sql("""
		SELECT tc.content, tc.parent as topic
		FROM `tabTopic Content` tc
		JOIN `tabVideo` v ON v.name = tc.content
		WHERE tc.content_type = 'Video'
		AND (v.lms_lesson IS NULL OR v.lms_lesson = '')
	""", as_dict=True)

	for row in video_topics:
		try:
			video = frappe.get_doc("Video", row.content)
			if not is_sync_enabled(video):
				continue

			chapter = get_chapter_for_topic(row.topic)
			if not chapter:
				continue

			lesson = create_lesson_from_video(video, chapter)
			if lesson:
				frappe.db.set_value("Video", row.content, "lms_lesson", lesson, update_modified=False)
				count += 1
		except Exception as e:
			errors.append(f"Video {row.content}: {str(e)}")

	frappe.db.commit()
	return count


@frappe.whitelist()
def check_program_enrollments(program_name):
	"""Check if program has LMS enrollments before syncing"""
	program = frappe.get_doc("Program", program_name)

	if not program.lms_program:
		return {"has_enrollments": False, "enrollment_count": 0, "member_count": 0}

	# Check for program members
	lms_program = frappe.get_doc("LMS Program", program.lms_program)
	member_count = len(lms_program.program_members)

	# Check for course enrollments
	enrollment_count = 0
	for course_ref in lms_program.program_courses:
		enrollment_count += frappe.db.count("LMS Enrollment", {"course": course_ref.course})

	return {
		"has_enrollments": member_count > 0 or enrollment_count > 0,
		"enrollment_count": enrollment_count,
		"member_count": member_count,
		"lms_program": program.lms_program
	}


@frappe.whitelist()
def check_course_enrollments(course_name):
	"""Check if course has LMS enrollments before syncing"""
	course = frappe.get_doc("Course", course_name)

	if not course.lms_course:
		return {"has_enrollments": False, "enrollment_count": 0}

	enrollment_count = frappe.db.count("LMS Enrollment", {"course": course.lms_course})

	return {
		"has_enrollments": enrollment_count > 0,
		"enrollment_count": enrollment_count,
		"lms_course": course.lms_course
	}


@frappe.whitelist()
def sync_single_program(program_name, force=False):
	"""Sync a single program and all its contents to LMS"""
	from education_custom.lms_sync.program_sync import create_lms_program, sync_program_courses, update_lms_program

	program = frappe.get_doc("Program", program_name)

	if program.lms_program and frappe.db.exists("LMS Program", program.lms_program):
		# Already synced - update the program and its courses
		update_lms_program(program)
		sync_program_courses(program, program.lms_program)
		frappe.db.commit()
		return {"status": "updated", "lms_program": program.lms_program}

	# Create new LMS program
	lms_program = create_lms_program(program)
	if lms_program:
		frappe.db.set_value("Program", program_name, "lms_program", lms_program, update_modified=False)
		sync_program_courses(program, lms_program)
		frappe.db.commit()
		return {"status": "created", "lms_program": lms_program}

	return {"status": "failed"}


@frappe.whitelist()
def sync_single_course(course_name, force=False):
	"""Sync a single course and all its contents to LMS"""
	from education_custom.lms_sync.course_sync import create_lms_course, sync_course_topics, update_lms_course

	course = frappe.get_doc("Course", course_name)

	if course.lms_course and frappe.db.exists("LMS Course", course.lms_course):
		# Already synced - update the course and its topics
		update_lms_course(course)
		sync_course_topics(course, course.lms_course)
		frappe.db.commit()
		return {"status": "updated", "lms_course": course.lms_course}

	# Create new LMS course
	lms_course = create_lms_course(course)
	if lms_course:
		frappe.db.set_value("Course", course_name, "lms_course", lms_course, update_modified=False)
		sync_course_topics(course, lms_course)
		frappe.db.commit()
		return {"status": "created", "lms_course": lms_course}

	return {"status": "failed"}


@frappe.whitelist()
def get_student_lms_status(student_name):
	"""Check if a student is enrolled in LMS"""
	from education_custom.lms_sync.utils import get_user_for_student

	user = get_user_for_student(student_name)
	if not user:
		return {"is_enrolled": False, "lms_user": None, "enrollment_count": 0}

	# Check if user has any LMS enrollments
	enrollment_count = frappe.db.count("LMS Enrollment", {"member": user})

	return {
		"is_enrolled": enrollment_count > 0,
		"lms_user": user,
		"enrollment_count": enrollment_count
	}


@frappe.whitelist()
def enroll_student_to_lms(student_name):
	"""
	Enroll a student to LMS:
	1. Check if student has a user account
	2. Sync programs/courses to LMS if not already synced
	3. Enroll the student in all their programs/courses in LMS
	"""
	from education_custom.lms_sync.program_sync import (
		create_lms_program, sync_program_courses, add_member_to_program
	)
	from education_custom.lms_sync.utils import get_user_for_student

	student = frappe.get_doc("Student", student_name)

	# Get user for student
	user = get_user_for_student(student_name)
	if not user:
		return {
			"status": "error",
			"message": f"Student {student.student_name} does not have a linked user account. Please create a user first."
		}

	# Get all submitted program enrollments for this student
	enrollments = frappe.get_all(
		"Program Enrollment",
		filters={"student": student_name, "docstatus": 1},
		fields=["name", "program"]
	)

	if not enrollments:
		return {
			"status": "error",
			"message": "Student has no submitted program enrollments."
		}

	results = {
		"programs_synced": 0,
		"programs_enrolled": 0,
		"courses_enrolled": 0,
		"errors": []
	}

	for enrollment in enrollments:
		try:
			program = frappe.get_doc("Program", enrollment.program)

			# Sync program to LMS if not already synced
			if not program.lms_program or not frappe.db.exists("LMS Program", program.lms_program):
				lms_program = create_lms_program(program)
				if lms_program:
					frappe.db.set_value("Program", program.name, "lms_program", lms_program, update_modified=False)
					program.lms_program = lms_program
					sync_program_courses(program, lms_program)
					results["programs_synced"] += 1

			if not program.lms_program:
				results["errors"].append(f"Failed to sync program: {program.program_name}")
				continue

			# Add student as member to LMS Program
			add_member_to_program(user, program.lms_program)
			results["programs_enrolled"] += 1

			# Enroll in all courses under this program
			lms_program_doc = frappe.get_doc("LMS Program", program.lms_program)
			for course_ref in lms_program_doc.program_courses:
				try:
					# Check if already enrolled
					existing = frappe.db.exists("LMS Enrollment", {
						"member": user,
						"course": course_ref.course
					})
					if not existing:
						lms_enrollment = frappe.get_doc({
							"doctype": "LMS Enrollment",
							"member": user,
							"course": course_ref.course,
							"member_type": "Student",
							"education_program_enrollment": enrollment.name,
							"synced_from_education": 1
						})
						# Use flags to skip progress calculation during insert
						lms_enrollment.flags.ignore_progress_calculation = True
						lms_enrollment.insert(ignore_permissions=True)
						results["courses_enrolled"] += 1
					else:
						# Already enrolled, count it
						results["courses_enrolled"] += 1
				except Exception as e:
					# Try direct DB insert as fallback to avoid LMS validation issues
					try:
						if not frappe.db.exists("LMS Enrollment", {"member": user, "course": course_ref.course}):
							frappe.db.sql("""
								INSERT INTO `tabLMS Enrollment`
								(name, creation, modified, modified_by, owner, docstatus, member, course, member_type, progress, synced_from_education)
								VALUES (%s, NOW(), NOW(), %s, %s, 0, %s, %s, 'Student', 0, 1)
							""", (
								frappe.generate_hash("LMS Enrollment", 10),
								frappe.session.user,
								frappe.session.user,
								user,
								course_ref.course
							))
							results["courses_enrolled"] += 1
					except Exception as e2:
						results["errors"].append(f"Failed to enroll in course {course_ref.course}: {str(e)}")

			# Mark the program enrollment as synced
			frappe.db.set_value("Program Enrollment", enrollment.name, "lms_synced", 1, update_modified=False)

		except Exception as e:
			results["errors"].append(f"Error with program {enrollment.program}: {str(e)}")

	frappe.db.commit()

	if results["programs_enrolled"] > 0 or results["courses_enrolled"] > 0:
		results["status"] = "success"
		results["message"] = f"Enrolled in {results['programs_enrolled']} programs and {results['courses_enrolled']} courses."
		if results["programs_synced"] > 0:
			results["message"] += f" ({results['programs_synced']} programs synced to LMS)"
	else:
		results["status"] = "error"
		results["message"] = "Failed to enroll in any programs or courses."

	return results
