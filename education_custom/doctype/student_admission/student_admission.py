from education.education.doctype.student_admission.student_admission import StudentAdmission as CoreStudentAdmission
import education_custom.utils as utils

class StudentAdmission(CoreStudentAdmission):

    def get_context(self, context):
        # call core logic first
        super().get_context(context)
        # expose utils to Jinja
        context.education_custom = {
            "utils": utils
        }
        # override template
        context.template = (
            "education_custom/templates/doctype/student_admission/student_admission.html"
        )

        return context
