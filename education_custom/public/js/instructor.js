frappe.ui.form.on('Instructor', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Show "Create as User" button only if instructor doesn't have a user linked
            if (!frm.doc.user && frm.doc.email) {
                // Check if a user with this email already exists
                frappe.db.exists('User', frm.doc.email).then(exists => {
                    if (exists) {
                        // User exists, offer to link
                        frm.add_custom_button(__('Link Existing User'), function() {
                            frappe.confirm(
                                __('A user with email {0} already exists. Do you want to link this instructor to that user?', [frm.doc.email]),
                                function() {
                                    frm.set_value('user', frm.doc.email);
                                    frm.save();
                                }
                            );
                        }, __('Create'));
                    } else {
                        // No user exists, show Create as User button
                        frm.add_custom_button(__('Create as User'), function() {
                            // Build full name from instructor_name
                            let full_name = frm.doc.instructor_name || '';
                            let name_parts = full_name.trim().split(' ');
                            let first_name = name_parts[0] || '';
                            let last_name = name_parts.slice(1).join(' ') || '';

                            // Create new User document with pre-filled values
                            frappe.model.with_doctype('User', function() {
                                let new_doc = frappe.model.get_new_doc('User');
                                new_doc.email = frm.doc.email;
                                new_doc.first_name = first_name;
                                new_doc.last_name = last_name;
                                new_doc.full_name = full_name;
                                new_doc.send_welcome_email = 1;
                                new_doc.user_type = 'System User';
                                new_doc.role_profile_name = 'Instructor';
                                new_doc.module_profile = 'Instructor';

                                frappe.set_route('Form', 'User', new_doc.name);
                            });
                        }, __('Create'));
                    }
                });
            } else if (frm.doc.user) {
                // User is linked, show button to view user
                frm.add_custom_button(__('View User'), function() {
                    frappe.set_route('Form', 'User', frm.doc.user);
                }, __('View'));
            }
        }
    },

    // When user is selected, validate it
    user: function(frm) {
        if (frm.doc.user && !frm.doc.email) {
            // Fetch email from user if not set
            frappe.db.get_value('User', frm.doc.user, 'email', function(r) {
                if (r && r.email) {
                    frm.set_value('email', r.email);
                }
            });
        }
    }
});
