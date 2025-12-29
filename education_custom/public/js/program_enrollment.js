frappe.ui.form.on('Program Enrollment', {
	refresh: function(frm) {
		// Only show button for submitted enrollments
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Sync to LMS'), function() {
				frappe.call({
					method: 'education_custom.lms_sync.enrollment_sync.resync_enrollment_to_lms',
					args: { program_enrollment_name: frm.doc.name },
					freeze: true,
					freeze_message: __('Syncing enrollments to LMS...'),
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: r.message.message,
								indicator: 'green'
							});
							frm.reload_doc();
						}
					},
					error: function(r) {
						frappe.show_alert({
							message: __('Sync failed. Check console for details.'),
							indicator: 'red'
						});
					}
				});
			}, __('LMS'));

			// Add link to view LMS enrollments if synced
			if (frm.doc.lms_synced) {
				frm.add_custom_button(__('View LMS Enrollments'), function() {
					frappe.set_route('List', 'LMS Enrollment', {
						'education_program_enrollment': frm.doc.name
					});
				}, __('LMS'));
			}
		}
	}
});
