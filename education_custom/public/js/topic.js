frappe.ui.form.on('Topic', {
	refresh: function(frm) {
		// Add link to LMS Chapter if exists - only for users with Content Sync role
		if (!frm.is_new() && frm.doc.lms_chapter && has_content_sync_role()) {
			frm.add_custom_button(__('Open in LMS'), function() {
				frappe.set_route('Form', 'Course Chapter', frm.doc.lms_chapter);
			}, __('LMS'));
		}
	}
});

function has_content_sync_role() {
	return frappe.user_roles.includes('Content Sync') ||
		frappe.user_roles.includes('System Manager') ||
		frappe.user_roles.includes('Administrator');
}
