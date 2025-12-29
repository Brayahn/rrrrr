frappe.ui.form.on('Education Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__('Sync All to LMS'), function() {
			frappe.confirm(
				__('This will sync all Programs, Courses, Topics, Articles, and Videos to LMS. Continue?'),
				function() {
					frappe.call({
						method: 'education_custom.lms_sync.sync_all.sync_all_to_lms',
						freeze: true,
						freeze_message: __('Syncing all content to LMS... This may take a while.'),
						callback: function(r) {
							if (r.message) {
								let msg = `
									<b>Sync Complete:</b><br>
									Programs: ${r.message.programs}<br>
									Courses: ${r.message.courses}<br>
									Topics: ${r.message.topics}<br>
									Articles: ${r.message.articles}<br>
									Videos: ${r.message.videos}
								`;
								if (r.message.errors && r.message.errors.length > 0) {
									msg += `<br><br><b>Errors (${r.message.errors.length}):</b><br>`;
									msg += r.message.errors.slice(0, 5).join('<br>');
									if (r.message.errors.length > 5) {
										msg += `<br>... and ${r.message.errors.length - 5} more`;
									}
								}
								frappe.msgprint({
									title: __('LMS Sync Results'),
									message: msg,
									indicator: r.message.errors.length > 0 ? 'orange' : 'green'
								});
							}
						}
					});
				}
			);
		}, __('LMS'));
	}
});
