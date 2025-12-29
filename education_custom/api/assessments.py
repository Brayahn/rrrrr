import frappe
from frappe import _


def get_student_for_user():
    """Get the student record linked to the current user."""
    if frappe.session.user == "Guest":
        return None

    # Try to find student by user field first
    student = frappe.db.get_value("Student", {"user": frappe.session.user}, "name")

    # If not found, try by email
    if not student:
        student = frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")

    return student


@frappe.whitelist()
def get_student_assessment_plans():
    """
    Get assessment plans for the currently logged in student.
    Returns upcoming and past assessment plans for student's enrolled courses.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your assessment plans"), frappe.AuthenticationError)

    student = get_student_for_user()

    if not student:
        return {
            "success": False,
            "message": _("No student record found for your account"),
            "upcoming": [],
            "past": []
        }

    # Get student's enrolled student groups
    student_groups = frappe.db.sql("""
        SELECT DISTINCT sgs.parent
        FROM `tabStudent Group Student` sgs
        WHERE sgs.student = %s
        AND sgs.active = 1
    """, student, as_dict=True)

    group_names = [sg.parent for sg in student_groups]

    if not group_names:
        return {
            "success": True,
            "student_name": frappe.db.get_value("Student", student, "student_name"),
            "upcoming": [],
            "past": [],
            "message": _("No enrolled student groups found")
        }

    # Get assessment plans for these student groups
    plans = frappe.db.sql("""
        SELECT
            ap.name,
            ap.assessment_name,
            ap.student_group,
            ap.course,
            ap.program,
            ap.schedule_date,
            ap.from_time,
            ap.to_time,
            ap.room,
            ap.examiner_name,
            ap.maximum_assessment_score,
            ap.docstatus
        FROM `tabAssessment Plan` ap
        WHERE ap.student_group IN %s
        AND ap.docstatus = 1
        ORDER BY ap.schedule_date DESC
    """, [group_names], as_dict=True)

    today = frappe.utils.today()
    upcoming = []
    past = []

    for plan in plans:
        plan.schedule_date_formatted = frappe.utils.formatdate(plan.schedule_date)
        plan.from_time_formatted = str(plan.from_time)[:5] if plan.from_time else ""
        plan.to_time_formatted = str(plan.to_time)[:5] if plan.to_time else ""

        if str(plan.schedule_date) >= today:
            upcoming.append(plan)
        else:
            past.append(plan)

    # Sort upcoming by date ascending, past by date descending
    upcoming.sort(key=lambda x: x.schedule_date)

    return {
        "success": True,
        "student_name": frappe.db.get_value("Student", student, "student_name"),
        "upcoming": upcoming,
        "past": past
    }


@frappe.whitelist()
def get_student_assessment_results():
    """
    Get assessment results for the currently logged in student.
    Returns all submitted assessment results with scores and grades.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your assessment results"), frappe.AuthenticationError)

    student = get_student_for_user()

    if not student:
        return {
            "success": False,
            "message": _("No student record found for your account"),
            "results": [],
            "summary": {}
        }

    # Get student details
    student_doc = frappe.get_doc("Student", student)

    # Get all submitted assessment results for this student
    results = frappe.db.sql("""
        SELECT
            ar.name,
            ar.assessment_plan,
            ar.course,
            ar.program,
            ar.academic_year,
            ar.academic_term,
            ar.student_group,
            ar.total_score,
            ar.maximum_score,
            ar.grade,
            ar.comment,
            ar.docstatus,
            ap.assessment_name,
            ap.schedule_date,
            ap.assessment_group,
            ap.grading_scale
        FROM `tabAssessment Result` ar
        LEFT JOIN `tabAssessment Plan` ap ON ar.assessment_plan = ap.name
        WHERE ar.student = %s
        AND ar.docstatus = 1
        ORDER BY ap.schedule_date DESC, ar.modified DESC
    """, student, as_dict=True)

    # Build a cache of grading scale descriptions
    grading_scales = {}
    for result in results:
        if result.grading_scale and result.grading_scale not in grading_scales:
            # Get all grade intervals for this grading scale
            intervals = frappe.get_all(
                "Grading Scale Interval",
                filters={"parent": result.grading_scale},
                fields=["grade_code", "grade_description"],
                order_by="threshold desc"
            )
            grading_scales[result.grading_scale] = {
                i.grade_code: i.grade_description for i in intervals
            }

    # Calculate summary statistics
    total_assessments = len(results)
    total_score = sum(r.total_score or 0 for r in results)
    total_max_score = sum(r.maximum_score or 0 for r in results)
    average_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0

    # Format results
    for result in results:
        result.schedule_date_formatted = frappe.utils.formatdate(result.schedule_date) if result.schedule_date else ""
        result.percentage = round((result.total_score / result.maximum_score * 100), 1) if result.maximum_score else 0

        # Get grade description from grading scale
        result.grade_description = ""
        if result.grade and result.grading_scale and result.grading_scale in grading_scales:
            result.grade_description = grading_scales[result.grading_scale].get(result.grade, "")

        # Get result details (criteria scores)
        result.details = frappe.get_all(
            "Assessment Result Detail",
            filters={"parent": result.name},
            fields=["assessment_criteria", "score", "maximum_score", "grade"],
            order_by="idx"
        )

        # Add grade descriptions to details as well
        for detail in result.details:
            detail.grade_description = ""
            if detail.grade and result.grading_scale and result.grading_scale in grading_scales:
                detail.grade_description = grading_scales[result.grading_scale].get(detail.grade, "")

    # Group results by course
    results_by_course = {}
    for result in results:
        course = result.course or "Uncategorized"
        if course not in results_by_course:
            results_by_course[course] = []
        results_by_course[course].append(result)

    return {
        "success": True,
        "student_name": student_doc.student_name,
        "student_id": student,
        "results": results,
        "results_by_course": results_by_course,
        "summary": {
            "total_assessments": total_assessments,
            "total_score": round(total_score, 1),
            "total_max_score": round(total_max_score, 1),
            "average_percentage": round(average_percentage, 1)
        }
    }
