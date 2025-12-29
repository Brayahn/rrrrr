frappe.ui.form.on('Fees', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.student) {
            // Button to view all payment entries for the student
            frm.add_custom_button(__('Student Payments'), function() {
                frappe.set_route('List', 'Payment Entry', {
                    'party_type': 'Student',
                    'party': frm.doc.student
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

                        // Get the default letterhead from the company
                        let company = frm.doc.company || frappe.defaults.get_user_default('Company');

                        frappe.db.get_value('Company', company, 'default_letter_head', (r) => {
                            let letterhead = r && r.default_letter_head ? r.default_letter_head : '';

                            let print_url = frappe.urllib.get_full_url(
                                '/printview?doctype=Student&name=' + encodeURIComponent(frm.doc.student) +
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
