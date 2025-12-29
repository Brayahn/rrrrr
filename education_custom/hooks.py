app_name = "education_custom"
app_title = "Collage Custom"
app_publisher = "Silvano"
app_description = "collage custom"
app_email = "Silvanussigei1996@gmail.com"
app_license = "mit"

fixtures = [
    # =============================================
    # CUSTOM FIELDS - All customizations
    # =============================================
    {"dt": "Custom Field", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    # Custom fields on education/LMS doctypes (regardless of module)
    {"dt": "Custom Field", "filters": [["dt", "in", [
        "Student", "Student Applicant", "Program", "Course", "Topic", "Article", "Video",
        "Program Enrollment", "Course Enrollment", "Fees", "Fee Structure", "Fee Component",
        "Student Admission", "Assessment Plan", "Assessment Result", "Assessment Criteria",
        "Instructor", "Student Group", "Student Attendance", "Academic Year", "Academic Term",
        "LMS Course", "LMS Program", "Course Chapter", "Course Lesson", "LMS Batch",
        "LMS Enrollment", "LMS Settings", "Education Settings"
    ]]]},

    # =============================================
    # PROPERTY SETTERS - Field modifications
    # =============================================
    {"dt": "Property Setter", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Property Setter", "filters": [["doc_type", "in", [
        "Student", "Student Applicant", "Program", "Course", "Topic",
        "Program Enrollment", "Course Enrollment", "Fees", "Fee Structure",
        "Student Admission", "Instructor", "Student Group", "Academic Year", "Academic Term",
        "LMS Course", "LMS Program", "Course Chapter", "Course Lesson"
    ]]]},

    # =============================================
    # CLIENT SCRIPTS - Custom JS
    # =============================================
    {"dt": "Client Script", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Client Script", "filters": [["dt", "in", [
        "Student", "Student Applicant", "Program", "Course", "Fees", "Fee Structure",
        "Program Enrollment", "Student Admission", "Instructor",
        "LMS Course", "LMS Program", "Course Chapter", "Course Lesson"
    ]]]},

    # =============================================
    # SERVER SCRIPTS - Server-side automation
    # =============================================
    {"dt": "Server Script", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Server Script", "filters": [["reference_doctype", "in", [
        "Student", "Student Applicant", "Program", "Course", "Fees", "Fee Structure",
        "Program Enrollment", "Student Admission", "LMS Course", "LMS Program"
    ]]]},

    # =============================================
    # WEB FORMS - All custom web forms
    # =============================================
    {"dt": "Web Form", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Web Form", "filters": [["doc_type", "in", [
        "Student", "Student Applicant", "Program Enrollment", "Fees",
        "Student Admission", "Course Enrollment", "LMS Enrollment"
    ]]]},
    # Include all custom web forms
    {"dt": "Web Form", "filters": [["is_standard", "=", 0]]},

    # =============================================
    # WEB PAGES - Custom pages
    # =============================================
    {"dt": "Web Page", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    # All non-standard web pages
    {"dt": "Web Page", "filters": [["is_standard", "=", 0]]},

    # =============================================
    # PRINT FORMATS / PRINT TEMPLATES
    # =============================================
    {"dt": "Print Format", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Print Format", "filters": [["doc_type", "in", [
        "Student", "Student Applicant", "Fees", "Fee Structure", "Program Enrollment",
        "Student Admission", "Assessment Result", "Assessment Plan", "Student Group"
    ]]]},
    # All custom print formats
    {"dt": "Print Format", "filters": [["standard", "=", "No"]]},

    # =============================================
    # WEBSITE CONFIGURATION
    # =============================================
    {"dt": "Website Settings"},
    {"dt": "Navbar Settings"},
    {"dt": "Website Theme", "filters": [["custom", "=", 1]]},
    {"dt": "Website Sidebar"},
    {"dt": "Website Script"},
    {"dt": "Color"},

    # =============================================
    # ROLES AND PERMISSIONS
    # =============================================
    {"dt": "Role", "filters": [["is_custom", "=", 1]]},
    {"dt": "Role Profile"},
    {"dt": "Module Profile"},
    {"dt": "Custom DocPerm"},

    # =============================================
    # WORKFLOWS
    # =============================================
    {"dt": "Workflow", "filters": [["document_type", "in", [
        "Student Applicant", "Student", "Program Enrollment", "Fees",
        "Student Admission", "Assessment Result", "Course Enrollment",
        "LMS Enrollment", "LMS Batch"
    ]]]},
    {"dt": "Workflow State"},
    {"dt": "Workflow Action Master"},

    # =============================================
    # NOTIFICATIONS & EMAIL
    # =============================================
    {"dt": "Notification", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Notification", "filters": [["document_type", "in", [
        "Student Applicant", "Student", "Program Enrollment", "Fees",
        "Student Admission", "LMS Enrollment"
    ]]]},
    {"dt": "Email Template", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Email Template", "filters": [["name", "like", "%student%"]]},
    {"dt": "Email Template", "filters": [["name", "like", "%admission%"]]},
    {"dt": "Email Template", "filters": [["name", "like", "%enrollment%"]]},
    {"dt": "Email Template", "filters": [["name", "like", "%fee%"]]},

    # =============================================
    # REPORTS & DASHBOARDS
    # =============================================
    {"dt": "Report", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Report", "filters": [["is_standard", "=", "No"], ["ref_doctype", "in", [
        "Student", "Student Applicant", "Program Enrollment", "Fees", "Course Enrollment"
    ]]]},
    {"dt": "Dashboard", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Dashboard Chart", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Number Card", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},

    # =============================================
    # EDUCATION MASTER DATA (Non-Transactional)
    # =============================================
    {"dt": "Academic Year"},
    {"dt": "Academic Term"},
    {"dt": "Education Settings"},
    {"dt": "Grading Scale"},
    {"dt": "Assessment Criteria"},
    {"dt": "Assessment Criteria Group"},
    {"dt": "Fee Category"},
    {"dt": "Student Category"},
    {"dt": "Student Batch Name"},
    {"dt": "Room"},
    {"dt": "Course Scheduling Tool"},

    # =============================================
    # LMS CONFIGURATION (Non-Transactional)
    # =============================================
    {"dt": "LMS Settings"},
    {"dt": "LMS Category"},

    # =============================================
    # PORTAL SETTINGS
    # =============================================
    {"dt": "Portal Menu Item"},
    {"dt": "Portal Settings"},
    {"dt": "Homepage"},
    {"dt": "Homepage Section"},

    # =============================================
    # WORKSPACE CUSTOMIZATION
    # =============================================
    {"dt": "Workspace", "filters": [["module", "in", ["Education Custom", "Education", "LMS"]]]},
    {"dt": "Workspace", "filters": [["for_user", "!=", ""]]},

    # =============================================
    # DOCUMENT TEMPLATES
    # =============================================
    {"dt": "Letter Head"},
    {"dt": "Print Style"},
    {"dt": "Address Template"},
    {"dt": "Terms and Conditions", "filters": [["name", "like", "%student%"]]},
    {"dt": "Terms and Conditions", "filters": [["name", "like", "%admission%"]]},
    {"dt": "Terms and Conditions", "filters": [["name", "like", "%fee%"]]},

    # =============================================
    # TRANSLATIONS
    # =============================================
    {"dt": "Translation"},

    # =============================================
    # CUSTOM DOCTYPES FROM THIS APP
    # =============================================
    {"dt": "DocType", "filters": [["module", "=", "Education Custom"], ["custom", "=", 1]]},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "education_custom",
# 		"logo": "/assets/education_custom/logo.png",
# 		"title": "Collage Custom",
# 		"route": "/education_custom",
# 		"has_permission": "education_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/education_custom/css/education_custom.css"
# app_include_js = "/assets/education_custom/js/education_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/education_custom/css/education_custom.css"
# web_include_js = "/assets/education_custom/js/education_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "education_custom/public/scss/website"

# include js, css files in header of web form
webform_include_js = {
    "student-applicant": "public/js/student_applicant_webform.js",
    "student-application-form": "public/js/student_applicant_webform.js",
    "student-application": "public/js/student_applicant_webform.js",
    "fee-structure": "public/js/fee_structure_webform.js"
}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Student Applicant": "public/js/student_applicant.js",
    "Fees": "public/js/fees.js",
    "Student": "public/js/student.js",
    "Instructor": "public/js/instructor.js",
    "Program": "public/js/program.js",
    "Program Enrollment": "public/js/program_enrollment.js",
    "Course": "public/js/course.js",
    "Topic": "public/js/topic.js",
    "LMS Program": "public/js/lms_program.js",
    "LMS Course": "public/js/lms_course.js",
    "Education Settings": "public/js/education_settings.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "education_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Override DocType Templates
# --------------------------
# Website Generator ,pages Portal pages ,Web routes defined by a controller
override_doctype_templates = {
    "Student Admission": "education_custom/templates/doctype/student_admission/student_admission.html",
}

# Portal Menu Items
# -----------------
# Add custom pages to the portal sidebar
# portal_menu_items = [
#     {"title": "Fees Report", "route": "/fees-report", "reference_doctype": "Fees", "role": "Student"},
#     {"title": "Assessment Plans", "route": "/assessment-plans", "reference_doctype": "Assessment Plan", "role": "Student"},
#     {"title": "Assessment Results", "route": "/assessment-results", "reference_doctype": "Assessment Result", "role": "Student"},
# ]
# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
		"education_custom.utils.get_fee_structure_details",
		"education_custom.utils.get_fee_structure_for_program"
	]
}

# Installation
# ------------

# before_install = "education_custom.install.before_install"
# after_install = "education_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "education_custom.uninstall.before_uninstall"
# after_uninstall = "education_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "education_custom.utils.before_app_install"
# after_app_install = "education_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "education_custom.utils.before_app_uninstall"
# after_app_uninstall = "education_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "education_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Program Enrollment": "education_custom.permissions.program_enrollment_query_conditions",
	"Course Enrollment": "education_custom.permissions.course_enrollment_query_conditions",
	"Student": "education_custom.permissions.student_query_conditions",
	"Fees": "education_custom.permissions.fees_query_conditions",
	"Course": "education_custom.permissions.course_query_conditions",
	"Program": "education_custom.permissions.program_query_conditions",
}

has_permission = {
	"Program Enrollment": "education_custom.permissions.program_enrollment_has_permission",
	"Course Enrollment": "education_custom.permissions.course_enrollment_has_permission",
	"Student": "education_custom.permissions.student_has_permission",
	"Fees": "education_custom.permissions.fees_has_permission",
	"Course": "education_custom.permissions.course_has_permission",
	"Program": "education_custom.permissions.program_has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# "ToDo": "custom_app.overrides.CustomToDo"
	"Student Admission": "education_custom.doctype.student_admission.student_admission.StudentAdmission",
	"Fee Structure": "education_custom.doctype.fee_structure.fee_structure.FeeStructure"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# Education -> LMS sync
	"Program": {
		"after_insert": "education_custom.lms_sync.program_sync.sync_program",
		"on_update": "education_custom.lms_sync.program_sync.update_program",
		"on_trash": "education_custom.lms_sync.program_sync.delete_program",
	},
	"Course": {
		"after_insert": "education_custom.lms_sync.course_sync.sync_course",
		"on_update": "education_custom.lms_sync.course_sync.update_course",
		"on_trash": "education_custom.lms_sync.course_sync.delete_course",
	},
	"Topic": {
		"after_insert": "education_custom.lms_sync.topic_sync.sync_topic",
		"on_update": "education_custom.lms_sync.topic_sync.update_topic",
		"on_trash": "education_custom.lms_sync.topic_sync.delete_topic",
	},
	"Article": {
		"after_insert": "education_custom.lms_sync.content_sync.sync_article",
		"on_update": "education_custom.lms_sync.content_sync.update_article",
		"on_trash": "education_custom.lms_sync.content_sync.delete_article",
	},
	"Video": {
		"after_insert": "education_custom.lms_sync.content_sync.sync_video",
		"on_update": "education_custom.lms_sync.content_sync.update_video",
		"on_trash": "education_custom.lms_sync.content_sync.delete_video",
	},
	"Program Enrollment": {
		"on_submit": "education_custom.lms_sync.enrollment_sync.sync_enrollment",
		"on_cancel": "education_custom.lms_sync.enrollment_sync.cancel_enrollment",
	},
	# LMS -> Education reverse sync
	"Course Lesson": {
		"on_update": "education_custom.lms_sync.reverse_sync.sync_lesson_to_education",
	},
	"Course Chapter": {
		"on_update": "education_custom.lms_sync.reverse_sync.sync_chapter_to_topic",
	},
	"LMS Course": {
		"on_update": "education_custom.lms_sync.reverse_sync.sync_course_to_education",
	},
	"LMS Program": {
		"on_update": "education_custom.lms_sync.reverse_sync.sync_program_to_education",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"education_custom.tasks.all"
# 	],
# 	"daily": [
# 		"education_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"education_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"education_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"education_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "education_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "education_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "education_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["education_custom.utils.before_request"]
# after_request = ["education_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["education_custom.utils.before_job"]
# after_job = ["education_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"education_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

