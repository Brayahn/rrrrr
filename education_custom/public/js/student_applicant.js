frappe.ui.form.on('Student Applicant', {
    refresh: function(frm) {
        // Set up the program filter based on branch
        frm.set_query('program', function() {
            if (!frm.doc.custom_branch) {
                frappe.msgprint(__('Please select a Branch first'));
                return { filters: { name: '' } }; // Returns no results
            }

            return {
                query: 'education_custom.api.get_programs_by_branch',
                filters: {
                    branch: frm.doc.custom_branch
                }
            };
        });
    },

    custom_branch: function(frm) {
        // Clear program when branch changes
        frm.set_value('program', '');
    }
});
