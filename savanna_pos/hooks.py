from .savanna_pos.doctype.doctype_names_mapping import (
    IMPORTED_ITEMS_STATUS_DOCTYPE_NAME,
    ITEM_TYPE_DOCTYPE_NAME,
    PRODUCT_TYPE_DOCTYPE_NAME,
    ROUTES_TABLE_DOCTYPE_NAME,
)

# OAuth Bearer Tokens are now used instead of JWT tokens
# No monkey patching needed as Frappe natively supports OAuth Bearer Tokens

app_name = "savanna_pos"
app_title = "Savanna POS"
app_publisher = "Navari Ltd"
app_description = "This app works to integrate ERPNext with KRA's eTIMS via Slade360 Advantage to allow for the sharing of information with the revenue authority."
app_email = "support@navari.co.ke"
app_license = "GNU Affero General Public License v3.0"
required_apps = ["erpnext"]


# Fixtures
# --------
fixtures = [
    {"dt": IMPORTED_ITEMS_STATUS_DOCTYPE_NAME},
    {"dt": ROUTES_TABLE_DOCTYPE_NAME},
    {"dt": ITEM_TYPE_DOCTYPE_NAME},
    {"dt": PRODUCT_TYPE_DOCTYPE_NAME},
    # {
    #     "dt": "Custom Field",
    #     "filters": [
    #         ["module", "=", "Savanna POS"]
    #     ],
    # },
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/savanna_pos/css/savanna_pos.css"
# app_include_js = "/assets/savanna_pos/js/savanna_pos.js"

# include js, css files in header of web template
# web_include_css = "/assets/savanna_pos/css/savanna_pos.css"
# web_include_js = "/assets/savanna_pos/js/savanna_pos.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "savanna_pos/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice": "savanna_pos/overrides/client/sales_invoice.js",
    "Purchase Invoice": "savanna_pos/overrides/client/purchase_invoice.js",
    "Customer": "savanna_pos/overrides/client/customer.js",
    "Supplier": "savanna_pos/overrides/client/supplier.js",
    "Item": "savanna_pos/overrides/client/items.js",
    "BOM": "savanna_pos/overrides/client/bom.js",
    "Branch": "savanna_pos/overrides/client/branch.js",
    "UOM": "savanna_pos/overrides/client/uom.js",
    # "Warehouse": "savanna_pos/overrides/client/warehouse.js",
    "Mode of Payment": "savanna_pos/overrides/client/mode_of_payment.js",
    "Stock Ledger Entry": "savanna_pos/overrides/client/stock_ledger_entry.js",
    # "Price List": "savanna_pos/overrides/client/price_list.js",
    # "Item Price": "savanna_pos/overrides/client/item_price.js",
}

doctype_list_js = {
    "Item": "savanna_pos/overrides/client/items_list.js",
    "Sales Invoice": "savanna_pos/overrides/client/sales_invoice_list.js",
    "Branch": "savanna_pos/overrides/client/branch_list.js",
    "Customer": "savanna_pos/overrides/client/customer_list.js",
    "UOM": "savanna_pos/overrides/client/uom_list.js",
    # "Warehouse": "savanna_pos/overrides/client/warehouse_list.js",
    "Mode of Payment": "savanna_pos/overrides/client/mode_of_payment_list.js",
    "Supplier": "savanna_pos/overrides/client/supplier_list.js",
    # "Price List": "savanna_pos/overrides/client/price_list_list.js",
    # "Item Price": "savanna_pos/overrides/client/item_price_list.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "savanna_pos/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "savanna_pos.utils.jinja_methods",
# 	"filters": "savanna_pos.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "savanna_pos.install.before_install"
# after_install = "savanna_pos.savanna_pos.patches.after_install.create_fields_and_links"

# Uninstallation
# ------------

# before_uninstall = "savanna_pos.uninstall.before_uninstall"
# after_uninstall = (
#     "savanna_pos.savanna_pos.setup.after_uninstall.after_uninstall"
# )

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "savanna_pos.utils.before_app_install"
# after_app_install = "savanna_pos.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "savanna_pos.utils.before_app_uninstall"
# after_app_uninstall = "savanna_pos.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "savanna_pos.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Scheduled Job Type": "savanna_pos.savanna_pos.overrides.server.scheduled_job_type.CustomScheduledJobType",
}
# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # 	"*": {
    # 		"on_update": "method",
    # 		"on_cancel": "method",
    # 		"on_trash": "method"
    # 	}
    "Sales Invoice": {
        "before_save": [
            "savanna_pos.savanna_pos.utils.before_save_"
        ],
        "on_submit": [
            "savanna_pos.savanna_pos.overrides.server.sales_invoice.on_submit"
        ],
        "validate": [
            "savanna_pos.savanna_pos.overrides.server.shared_overrides.validate"
        ],
        "before_cancel": [
            "savanna_pos.savanna_pos.overrides.server.sales_invoice.before_cancel"
        ],
        "before_update_after_submit": [
            "savanna_pos.savanna_pos.utils.before_save_"
        ],
    },
    "Purchase Invoice": {
        "before_save": [
            "savanna_pos.savanna_pos.utils.before_save_"
        ],
        "on_submit": [
            "savanna_pos.savanna_pos.overrides.server.purchase_invoice.on_submit"
        ],
        "validate": [
            "savanna_pos.savanna_pos.overrides.server.purchase_invoice.validate"
        ],
        "before_cancel": [
            "savanna_pos.savanna_pos.overrides.server.sales_invoice.before_cancel"
        ],
    },
    "Item": {
        "validate": [
            "savanna_pos.savanna_pos.overrides.server.item.validate"
        ],
        "on_update": [
            "savanna_pos.savanna_pos.overrides.server.item.on_update"
        ],
        "on_trash": "savanna_pos.savanna_pos.overrides.server.item.prevent_item_deletion",
    },
    "BOM": {
        "on_submit": [
            "savanna_pos.savanna_pos.overrides.server.bom.on_submit"
        ]
    },
    "Supplier": {
        "on_update": [
            "savanna_pos.savanna_pos.overrides.server.supplier.on_update"
        ],
    },
    "Customer": {
        "on_update": [
            "savanna_pos.savanna_pos.overrides.server.customer.on_update"
        ],
        "validate": [
            "savanna_pos.savanna_pos.overrides.server.customer.validate"
        ],
    },
    "Stock Ledger Entry": {
        "on_update": [
            "savanna_pos.savanna_pos.overrides.server.stock_ledger_entry.on_update"
        ],
    },
    "POS Invoice": {
        "on_submit": [
            "savanna_pos.savanna_pos.overrides.server.pos_invoice.on_submit"
        ],
        "before_cancel": [
            "savanna_pos.savanna_pos.overrides.server.sales_invoice.before_cancel"
        ],
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "savanna_pos.savanna_pos.background_tasks.tasks.refresh_notices",
    ],
    "hourly": [
        # "savanna_pos.savanna_pos.background_tasks.tasks.send_sales_invoices_information",
        # "savanna_pos.savanna_pos.background_tasks.tasks.send_purchase_information",
        # "savanna_pos.savanna_pos.background_tasks.tasks.send_stock_information",
    ],
    "weekly": [
        "savanna_pos.savanna_pos.background_tasks.tasks.update_setting_passwords",
    ],
    "monthly": [
        "savanna_pos.savanna_pos.background_tasks.tasks.refresh_code_lists",
        # "savanna_pos.savanna_pos.background_tasks.tasks.search_organisations_request",
        "savanna_pos.savanna_pos.background_tasks.tasks.get_item_classification_codes",
    ],
}

after_migrate = ["savanna_pos.savanna_pos.patches.migrate_to_multi_company.execute"]

# Testing
# -------

# before_tests = "savanna_pos.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "savanna_pos.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "savanna_pos.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# CORS is handled at the server level (nginx/reverse proxy), so no custom CORS hooks needed
# before_request = ["savanna_pos.savanna_pos.utils.before_request"]
# after_request = ["savanna_pos.savanna_pos.utils.after_request"]

# Job Events
# ----------
# before_job = ["savanna_pos.utils.before_job"]
# after_job = ["savanna_pos.utils.after_job"]

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

# OAuth Bearer Tokens are handled natively by Frappe, no custom auth hooks needed
auth_hooks = []
