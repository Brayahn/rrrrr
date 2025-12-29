frappe.ready(function() {
    // Set up program filter based on branch for web form
    frappe.web_form.on('custom_branch', (field, value) => {
        // Clear program when branch changes
        frappe.web_form.set_value('program', '');
        hide_fees_button();

        // Update program options based on selected branch
        if (value) {
            update_program_options(value);
        } else {
            // Clear program options if no branch selected
            set_program_awesomplete_list([]);
        }
    });

    // Listen for program field changes to show/hide fees button
    frappe.web_form.on('program', (field, value) => {
        if (value) {
            show_fees_button(value);
        } else {
            hide_fees_button();
        }
    });

    // Also set up filtering when program field is focused/clicked
    let program_field = frappe.web_form.fields_dict.program;
    if (program_field && program_field.$input) {
        program_field.$input.on('focus', function() {
            let branch = frappe.web_form.get_value('custom_branch');
            if (!branch) {
                frappe.msgprint(__('Please select a Branch first'));
                return;
            }
            update_program_options(branch);
        });
    }

    // Initial load - if branch is already set, load programs
    let initial_branch = frappe.web_form.get_value('custom_branch');
    if (initial_branch) {
        update_program_options(initial_branch);
    }

    // Initial load - if program is already set, show fees button
    let initial_program = frappe.web_form.get_value('program');
    if (initial_program) {
        show_fees_button(initial_program);
    }
});

function update_program_options(branch) {
    frappe.call({
        method: 'education_custom.api.get_programs_by_branch',
        args: {
            doctype: 'Program',
            txt: '',
            searchfield: 'name',
            start: 0,
            page_len: 999,
            filters: { branch: branch }
        },
        callback: function(r) {
            if (r.message) {
                set_program_awesomplete_list(r.message);
            }
        }
    });
}

function set_program_awesomplete_list(programs) {
    let program_field = frappe.web_form.fields_dict.program;
    if (program_field && program_field.awesomplete) {
        // Format: [[name, program_name], ...] -> [{label: program_name, value: name}, ...]
        let list = programs.map(function(p) {
            return {
                label: p[1] || p[0],  // program_name or name
                value: p[0]            // name
            };
        });
        program_field.awesomplete.list = list;
    }
}

// ============================================
// Fees Button Functionality (Links to fee-structure page)
// ============================================

function show_fees_button(program) {
    // Remove existing button if any
    hide_fees_button();

    // Find the program field wrapper
    let program_field = frappe.web_form.fields_dict.program;
    if (!program_field || !program_field.$wrapper) return;

    // Get academic year from URL or student admission
    let urlParams = new URLSearchParams(window.location.search);
    let academic_year = urlParams.get('academic_year');
    let student_admission = urlParams.get('student_admission') ||
                           frappe.web_form.get_value('student_admission');

    // Build the fee structure page URL
    let feeUrl = '/fee-structure?program=' + encodeURIComponent(program);
    if (academic_year) {
        feeUrl += '&academic_year=' + encodeURIComponent(academic_year);
    }
    if (student_admission) {
        feeUrl += '&student_admission=' + encodeURIComponent(student_admission);
    }

    // Create the View Fees button (opens in new tab)
    let btn = $(`
        <a href="${feeUrl}" target="_blank" class="btn btn-sm btn-info view-fees-btn" style="margin-top: 8px; margin-right: 8px;">
            <i class="fa fa-money"></i> View Fees
        </a>
    `);

    // Insert button after the program field
    program_field.$wrapper.append(btn);
}

function hide_fees_button() {
    $('.view-fees-btn').remove();
}
