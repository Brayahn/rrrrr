frappe.ui.form.on('Program', {
	refresh: function(frm) {
		// Add Sync to LMS button - only for users with Content Sync role
		if (!frm.is_new() && has_content_sync_role()) {
			frm.add_custom_button(__('Sync to LMS'), function() {
				// First check for enrollments
				frappe.call({
					method: 'education_custom.lms_sync.sync_all.check_program_enrollments',
					args: { program_name: frm.doc.name },
					callback: function(r) {
						if (r.message && r.message.has_enrollments) {
							// Has enrollments - show confirmation
							let msg = __('This program has active LMS enrollments:') + '<br><br>';
							msg += '<b>' + __('Program Members') + ':</b> ' + r.message.member_count + '<br>';
							msg += '<b>' + __('Course Enrollments') + ':</b> ' + r.message.enrollment_count + '<br><br>';
							msg += __('Updating may affect enrolled students. Are you sure you want to continue?');

							frappe.confirm(msg, function() {
								// User confirmed - proceed with sync
								do_sync_program(frm);
							});
						} else {
							// No enrollments - proceed directly
							do_sync_program(frm);
						}
					}
				});
			}, __('LMS'));

			// Add link to LMS Program if exists
			if (frm.doc.lms_program) {
				frm.add_custom_button(__('Open in LMS'), function() {
					frappe.set_route('Form', 'LMS Program', frm.doc.lms_program);
				}, __('LMS'));
			}
		}
	}
});

function has_content_sync_role() {
	return frappe.user_roles.includes('Content Sync') ||
		frappe.user_roles.includes('System Manager') ||
		frappe.user_roles.includes('Administrator');
}

function do_sync_program(frm) {
	frappe.call({
		method: 'education_custom.lms_sync.sync_all.sync_single_program',
		args: { program_name: frm.doc.name },
		freeze: true,
		freeze_message: __('Syncing to LMS...'),
		callback: function(r) {
			if (r.message) {
				if (r.message.status === 'created') {
					frappe.show_alert({
						message: __('Program synced to LMS: {0}', [r.message.lms_program]),
						indicator: 'green'
					});
				} else if (r.message.status === 'updated') {
					frappe.show_alert({
						message: __('LMS Program updated successfully'),
						indicator: 'blue'
					});
				} else {
					frappe.show_alert({
						message: __('Sync failed'),
						indicator: 'red'
					});
				}
				frm.reload_doc();
			}
		}
	});
}
