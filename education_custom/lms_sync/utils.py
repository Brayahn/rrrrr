import re
import frappe
from frappe import _


def is_lms_installed():
	"""Check if LMS app is installed"""
	return "lms" in frappe.get_installed_apps()


def is_sync_enabled(doc):
	"""Check if sync is enabled for this document"""
	if not is_lms_installed():
		return False

	# Check if disable_lms_sync flag exists and is set
	if hasattr(doc, "disable_lms_sync") and doc.disable_lms_sync:
		return False

	return True


def html_to_markdown(html_content):
	"""
	Convert HTML content to Markdown for LMS Course Lesson
	Simple conversion for common HTML tags
	"""
	if not html_content:
		return ""

	content = html_content

	# Handle common HTML tags
	# Headers
	content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', content, flags=re.DOTALL)
	content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', content, flags=re.DOTALL)
	content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', content, flags=re.DOTALL)
	content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n', content, flags=re.DOTALL)
	content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1\n', content, flags=re.DOTALL)
	content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1\n', content, flags=re.DOTALL)

	# Bold and italic
	content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
	content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
	content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
	content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)

	# Links
	content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.DOTALL)

	# Images
	content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', content, flags=re.DOTALL)
	content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', content, flags=re.DOTALL)

	# Lists
	content = re.sub(r'<ul[^>]*>', '\n', content)
	content = re.sub(r'</ul>', '\n', content)
	content = re.sub(r'<ol[^>]*>', '\n', content)
	content = re.sub(r'</ol>', '\n', content)
	content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.DOTALL)

	# Paragraphs and line breaks
	content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
	content = re.sub(r'<br\s*/?>', '\n', content)
	content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', content, flags=re.DOTALL)

	# Code blocks
	content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```\n', content, flags=re.DOTALL)
	content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.DOTALL)

	# Blockquotes
	content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', content, flags=re.DOTALL)

	# Remove remaining HTML tags
	content = re.sub(r'<[^>]+>', '', content)

	# Clean up whitespace
	content = re.sub(r'\n{3,}', '\n\n', content)
	content = content.strip()

	# Decode HTML entities
	content = content.replace('&nbsp;', ' ')
	content = content.replace('&amp;', '&')
	content = content.replace('&lt;', '<')
	content = content.replace('&gt;', '>')
	content = content.replace('&quot;', '"')
	content = content.replace('&#39;', "'")

	return content


def markdown_to_html(markdown_content):
	"""
	Convert Markdown content to HTML for Education Article
	Simple conversion for common Markdown syntax
	"""
	if not markdown_content:
		return ""

	content = markdown_content

	# Code blocks (must be done before inline code)
	content = re.sub(r'```(\w*)\n(.*?)\n```', r'<pre><code>\2</code></pre>', content, flags=re.DOTALL)

	# Inline code
	content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

	# Headers (must be done before other processing)
	content = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', content, flags=re.MULTILINE)
	content = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', content, flags=re.MULTILINE)
	content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
	content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
	content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
	content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)

	# Bold and italic
	content = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', content)
	content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
	content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
	content = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', content)
	content = re.sub(r'__(.+?)__', r'<strong>\1</strong>', content)
	content = re.sub(r'_(.+?)_', r'<em>\1</em>', content)

	# Images (must be before links)
	content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', content)

	# Links
	content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)

	# Blockquotes
	content = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)

	# Unordered lists
	lines = content.split('\n')
	in_list = False
	result = []
	for line in lines:
		if re.match(r'^[-*+] ', line):
			if not in_list:
				result.append('<ul>')
				in_list = True
			item = re.sub(r'^[-*+] (.+)$', r'<li>\1</li>', line)
			result.append(item)
		else:
			if in_list:
				result.append('</ul>')
				in_list = False
			result.append(line)
	if in_list:
		result.append('</ul>')
	content = '\n'.join(result)

	# Ordered lists
	lines = content.split('\n')
	in_list = False
	result = []
	for line in lines:
		if re.match(r'^\d+\. ', line):
			if not in_list:
				result.append('<ol>')
				in_list = True
			item = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', line)
			result.append(item)
		else:
			if in_list:
				result.append('</ol>')
				in_list = False
			result.append(line)
	if in_list:
		result.append('</ol>')
	content = '\n'.join(result)

	# Horizontal rules
	content = re.sub(r'^---+$', r'<hr>', content, flags=re.MULTILINE)
	content = re.sub(r'^\*\*\*+$', r'<hr>', content, flags=re.MULTILINE)

	# Paragraphs - wrap standalone lines
	lines = content.split('\n')
	result = []
	for line in lines:
		stripped = line.strip()
		if stripped and not stripped.startswith('<'):
			result.append(f'<p>{stripped}</p>')
		else:
			result.append(line)
	content = '\n'.join(result)

	# Clean up empty paragraphs
	content = re.sub(r'<p>\s*</p>', '', content)

	# Clean up whitespace
	content = re.sub(r'\n{3,}', '\n\n', content)
	content = content.strip()

	return content


def get_youtube_id(url):
	"""Extract YouTube video ID from URL"""
	if not url:
		return None

	# Handle various YouTube URL formats
	patterns = [
		r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
		r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
	]

	for pattern in patterns:
		match = re.search(pattern, url)
		if match:
			return match.group(1)

	return None


def is_youtube_url(url):
	"""Check if URL is a YouTube video"""
	if not url:
		return False
	return 'youtube.com' in url or 'youtu.be' in url


def log_sync_error(doc, error, operation="sync"):
	"""Log sync error without blocking the original operation"""
	frappe.log_error(
		title=f"LMS Sync Error: {doc.doctype} {operation}",
		message=f"Document: {doc.name}\nError: {str(error)}\n\n{frappe.get_traceback()}"
	)


def get_lms_course_for_education_course(education_course):
	"""Get LMS Course linked to Education Course"""
	if not education_course:
		return None

	lms_course = frappe.db.get_value("Course", education_course, "lms_course")
	if lms_course and frappe.db.exists("LMS Course", lms_course):
		return lms_course
	return None


def get_chapter_for_topic(topic_name):
	"""Get Course Chapter linked to Education Topic"""
	if not topic_name:
		return None

	chapter = frappe.db.get_value("Topic", topic_name, "lms_chapter")
	if chapter and frappe.db.exists("Course Chapter", chapter):
		return chapter
	return None


def get_user_for_student(student_name):
	"""Get User record for a Student"""
	if not student_name:
		return None

	student = frappe.get_doc("Student", student_name)

	# First check if user field is set
	if student.user and frappe.db.exists("User", student.user):
		return student.user

	# Fall back to finding by email
	if student.student_email_id:
		user = frappe.db.get_value("User", {"email": student.student_email_id}, "name")
		if user:
			return user

	return None


def has_lms_enrollments(lms_course):
	"""Check if LMS Course has any enrollments"""
	if not lms_course:
		return False
	return frappe.db.count("LMS Enrollment", {"course": lms_course}) > 0


def has_lms_program_members(lms_program):
	"""Check if LMS Program has any members"""
	if not lms_program:
		return False

	program_doc = frappe.get_doc("LMS Program", lms_program)
	return len(program_doc.program_members) > 0
