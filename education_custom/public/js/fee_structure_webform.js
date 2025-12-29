frappe.ready(function() {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const program = urlParams.get('program');
    const academicYear = urlParams.get('academic_year');
    const studentAdmission = urlParams.get('student_admission');

    if (program && academicYear) {
        // Fetch fee structure for this program and academic year
        frappe.call({
            method: 'education_custom.api.get_fee_structure_for_program',
            args: {
                program: program,
                academic_year: academicYear
            },
            callback: function(r) {
                if (r.message) {
                    displayFeeStructure(r.message, program, academicYear, studentAdmission);
                } else {
                    displayNoFeeStructure(program);
                }
            },
            error: function() {
                displayError();
            }
        });
    }
});

function displayFeeStructure(fs, program, academicYear, studentAdmission) {
    // Hide the web form and show custom content
    const formWrapper = document.querySelector('.web-form-wrapper') ||
                        document.querySelector('.web-form') ||
                        document.querySelector('[data-web-form]');

    if (formWrapper) {
        formWrapper.style.display = 'none';
    }

    // Create custom display
    let html = `
        <div class="fee-structure-display">
            <div class="card mb-4">
                <div class="card-header" style="background-color: #5e64ff; color: white;">
                    <h4 class="mb-0">
                        <i class="fa fa-graduation-cap"></i> ${program}
                    </h4>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <strong>Academic Year:</strong> ${academicYear}
                        </div>
                    </div>

                    <h5 class="mt-4 mb-3">Fee Components</h5>
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped">
                            <thead style="background-color: #f8f9fa;">
                                <tr>
                                    <th style="width: 5%">#</th>
                                    <th style="width: 35%">Fee Category</th>
                                    <th style="width: 40%">Description</th>
                                    <th style="width: 20%" class="text-right">Amount</th>
                                </tr>
                            </thead>
                            <tbody>
    `;

    if (fs.components && fs.components.length > 0) {
        fs.components.forEach(function(comp, index) {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${comp.fees_category || comp.category || ''}</strong></td>
                    <td>${comp.description || '-'}</td>
                    <td class="text-right">${formatCurrency(comp.amount)}</td>
                </tr>
            `;
        });
    }

    html += `
                            </tbody>
                            <tfoot>
                                <tr style="background-color: #e3f2fd;">
                                    <th colspan="3" class="text-right">Total Amount</th>
                                    <th class="text-right">${formatCurrency(fs.total_amount)}</th>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>

            <div class="d-flex justify-content-between mt-4">
                <a href="javascript:history.back()" class="btn btn-secondary">
                    <i class="fa fa-arrow-left"></i> Back
                </a>
                <div>
                    <button type="button" class="btn btn-info mr-2" onclick="showFeesModal('${program.replace(/'/g, "\\'")}', '${academicYear.replace(/'/g, "\\'")}')">
                        <i class="fa fa-money"></i> View Fees
                    </button>
    `;

    if (studentAdmission) {
        html += `
                    <a href="/student-application-form?program=${encodeURIComponent(program)}&student_admission=${encodeURIComponent(studentAdmission)}&academic_year=${encodeURIComponent(academicYear)}"
                       class="btn btn-primary">
                        <i class="fa fa-edit"></i> Apply
                    </a>
        `;
    }

    html += `
                </div>
            </div>
        </div>
    `;

    // Insert the custom display
    const container = document.querySelector('.main-section') ||
                      document.querySelector('.container') ||
                      document.querySelector('main') ||
                      document.body;

    const displayDiv = document.createElement('div');
    displayDiv.innerHTML = html;

    if (formWrapper && formWrapper.parentNode) {
        formWrapper.parentNode.insertBefore(displayDiv, formWrapper);
    } else {
        container.appendChild(displayDiv);
    }
}

function displayNoFeeStructure(program) {
    const formWrapper = document.querySelector('.web-form-wrapper') ||
                        document.querySelector('.web-form') ||
                        document.querySelector('[data-web-form]');

    if (formWrapper) {
        formWrapper.style.display = 'none';
    }

    const html = `
        <div class="alert alert-info">
            <i class="fa fa-info-circle"></i> No fee structure found for <strong>${program}</strong>.
        </div>
        <a href="javascript:history.back()" class="btn btn-secondary">
            <i class="fa fa-arrow-left"></i> Back
        </a>
    `;

    const container = document.querySelector('.main-section') ||
                      document.querySelector('.container') ||
                      document.body;

    const displayDiv = document.createElement('div');
    displayDiv.innerHTML = html;

    if (formWrapper && formWrapper.parentNode) {
        formWrapper.parentNode.insertBefore(displayDiv, formWrapper);
    } else {
        container.appendChild(displayDiv);
    }
}

function displayError() {
    const html = `
        <div class="alert alert-danger">
            <i class="fa fa-exclamation-triangle"></i> Error loading fee structure. Please try again.
        </div>
        <a href="javascript:history.back()" class="btn btn-secondary">
            <i class="fa fa-arrow-left"></i> Back
        </a>
    `;

    const container = document.querySelector('.main-section') ||
                      document.querySelector('.container') ||
                      document.body;

    const displayDiv = document.createElement('div');
    displayDiv.innerHTML = html;
    container.appendChild(displayDiv);
}

function formatCurrency(value) {
    if (typeof frappe !== 'undefined' && frappe.format_currency) {
        return frappe.format_currency(value);
    }
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 2
    }).format(value || 0);
}

// ============================================
// Fees Modal Functionality
// ============================================

function createFeeModal() {
    // Only create if it doesn't exist
    if (document.getElementById('feeStructureModal')) return;

    const modal = document.createElement('div');
    modal.innerHTML = `
        <div class="modal fade" id="feeStructureModal" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header" style="background-color: #5e64ff; color: white;">
                        <h4 class="modal-title" id="feeModalTitle">Fee Structure</h4>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close" style="color: white;">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body" id="feeModalContent">
                        <p class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading...</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal.firstElementChild);
}

function showFeesModal(program, academicYear) {
    // Create modal if it doesn't exist
    createFeeModal();

    // Show loading state
    document.getElementById('feeModalTitle').textContent = 'Fee Structure - ' + program;
    document.getElementById('feeModalContent').innerHTML = '<p class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading fee structure...</p>';

    // Show the modal
    $('#feeStructureModal').modal('show');

    // Fetch and display fee structure
    frappe.call({
        method: 'education_custom.api.get_fee_structure_for_program',
        args: {
            program: program,
            academic_year: academicYear
        },
        callback: function(r) {
            if (r.message) {
                renderFeeModalContent(r.message);
            } else {
                document.getElementById('feeModalContent').innerHTML =
                    '<p class="text-muted text-center">No fee structure available for this program.</p>';
            }
        },
        error: function() {
            document.getElementById('feeModalContent').innerHTML =
                '<p class="text-danger text-center">Error loading fee structure. Please try again.</p>';
        }
    });
}

function renderFeeModalContent(fs) {
    let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead style="background-color: #f8f9fa;">
                    <tr>
                        <th style="width: 5%">#</th>
                        <th style="width: 35%">Fee Category</th>
                        <th style="width: 40%">Description</th>
                        <th style="width: 20%" class="text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (fs.components && fs.components.length > 0) {
        fs.components.forEach(function(comp, index) {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${comp.fees_category || comp.category || ''}</strong></td>
                    <td>${comp.description || '-'}</td>
                    <td class="text-right">${formatCurrency(comp.amount)}</td>
                </tr>
            `;
        });
    }

    html += `
                </tbody>
                <tfoot>
                    <tr style="background-color: #e3f2fd;">
                        <th colspan="3" class="text-right">Total Amount</th>
                        <th class="text-right">${formatCurrency(fs.total_amount)}</th>
                    </tr>
                </tfoot>
            </table>
        </div>
    `;

    document.getElementById('feeModalContent').innerHTML = html;
}
