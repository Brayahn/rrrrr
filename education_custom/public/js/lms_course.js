frappe.ui.form.on('LMS Course', {
	refresh: function(frm) {
		// Add link to Education Course if exists - only for users with Content Sync role
		if (!frm.is_new() && frm.doc.education_course && has_content_sync_role()) {
			frm.add_custom_button(__('Open in Education'), function() {
				frappe.set_route('Form', 'Course', frm.doc.education_course);
			}, __('Education'));
		}
	}
});

function has_content_sync_role() {
	return frappe.user_roles.includes('Content Sync') ||
		frappe.user_roles.includes('System Manager') ||
		frappe.user_roles.includes('Administrator');
}
