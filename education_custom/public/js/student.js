frappe.ui.form.on('Student', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Check if student doesn't have a user and is enrolled in a program
            if (!frm.doc.user && frm.doc.student_email_id) {
                // Check if a user with this email already exists
                frappe.db.exists('User', frm.doc.student_email_id).then(exists => {
                    if (exists) return; // User already exists, don't show button

                    // Check if student has any program enrollment
                    frappe.db.count('Program Enrollment', {
                        filters: { student: frm.doc.name }
                    }).then(count => {
                        if (count > 0) {
                            frm.add_custom_button(__('Create as Portal User'), function() {
                            // Build full name
                            let full_name = frm.doc.first_name || '';
                            if (frm.doc.middle_name) {
                                full_name += ' ' + frm.doc.middle_name;
                            }
                            if (frm.doc.last_name) {
                                full_name += ' ' + frm.doc.last_name;
                            }

                            // Create new User document with pre-filled values
                            frappe.model.with_doctype('User', function() {
                                let new_doc = frappe.model.get_new_doc('User');
                                new_doc.email = frm.doc.student_email_id;
                                new_doc.first_name = frm.doc.first_name;
                                new_doc.middle_name = frm.doc.middle_name;
                                new_doc.last_name = frm.doc.last_name;
                                new_doc.full_name = full_name.trim();
                                new_doc.send_welcome_email = 1;
                                new_doc.user_type = 'Website User';
                                frappe.set_route('Form', 'User', new_doc.name);
                            });
                        }, __('Create'));
                        }
                    });
                });
            }

            // Check if student is enrolled in LMS and show appropriate button
            frappe.call({
                method: 'education_custom.lms_sync.sync_all.get_student_lms_status',
                args: { student_name: frm.doc.name },
                callback: function(r) {
                    if (r.message && r.message.is_enrolled) {
                        // Show View in LMS button
                        frm.add_custom_button(__('View in LMS'), function() {
                            if (r.message.lms_user) {
                                // Open LMS user profile or courses page
                                window.open('/lms/courses', '_blank');
                            }
                        }, __('LMS'));
                    } else {
                        // Show Enroll in LMS button
                        frm.add_custom_button(__('Enroll in LMS'), function() {
                            frappe.call({
                                method: 'education_custom.lms_sync.sync_all.enroll_student_to_lms',
                                args: { student_name: frm.doc.name },
                                freeze: true,
                                freeze_message: __('Enrolling student in LMS...'),
                                callback: function(r) {
                                    if (r.message) {
                                        if (r.message.status === 'success') {
                                            let msg = r.message.message;
                                            if (r.message.errors && r.message.errors.length > 0) {
                                                msg += '<br><br><b>Warnings:</b><br>' + r.message.errors.join('<br>');
                                            }
                                            frappe.msgprint({
                                                title: __('LMS Enrollment'),
                                                message: msg,
                                                indicator: r.message.errors && r.message.errors.length > 0 ? 'orange' : 'green'
                                            });
                                            frm.reload_doc();
                                        } else {
                                            frappe.msgprint({
                                                title: __('LMS Enrollment Failed'),
                                                message: r.message.message,
                                                indicator: 'red'
                                            });
                                        }
                                    }
                                }
                            });
                        }, __('LMS'));
                    }
                }
            });

            // Button to view all payment entries for the student
            frm.add_custom_button(__('Student Payments'), function() {
                frappe.set_route('List', 'Payment Entry', {
                    'party_type': 'Student',
                    'party': frm.doc.name
                });
            }, __('View'));

            frm.add_custom_button(__('Generate Fees Statement'), function() {
                // Show dialog to select date range
                let dialog = new frappe.ui.Dialog({
                    title: __('Select Date Range'),
                    fields: [
                        {
                            fieldname: 'from_date',
                            fieldtype: 'Date',
                            label: __('From Date'),
                            reqd: 1,
                            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12)
                        },
                        {
                            fieldname: 'to_date',
                            fieldtype: 'Date',
                            label: __('To Date'),
                            reqd: 1,
                            default: frappe.datetime.get_today()
                        }
                    ],
                    primary_action_label: __('Generate'),
                    primary_action: function(values) {
                        dialog.hide();

                        // Get the default letterhead from the user's default company
                        let company = frappe.defaults.get_user_default('Company');

                        frappe.db.get_value('Company', company, 'default_letter_head', (r) => {
                            let letterhead = r && r.default_letter_head ? r.default_letter_head : '';

                            let print_url = frappe.urllib.get_full_url(
                                '/printview?doctype=Student&name=' + encodeURIComponent(frm.doc.name) +
                                '&format=' + encodeURIComponent('Fees Statement with Date Range') +
                                '&no_letterhead=0' +
                                '&letterhead=' + encodeURIComponent(letterhead) +
                                '&from_date=' + encodeURIComponent(values.from_date) +
                                '&to_date=' + encodeURIComponent(values.to_date) +
                                '&_lang=en'
                            );
                            window.open(print_url, '_blank');
                        });
                    }
                });
                dialog.show();
            }, __('View'));
        }
    }
});
