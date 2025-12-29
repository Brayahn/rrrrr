
import frappe
from lms.lms.doctype.lms_program.lms_program import LMSProgram

def test_route_fix():
    # Create a test LMS Program
    doc = frappe.new_doc("LMS Program")
    doc.title = "Test Program for Route"
    doc.published = 1
    # Check if route is not set initially
    
    doc.save()
    
    if doc.route == "lms-programs/test-program-for-route":
        print("SUCCESS: Route generated correctly: " + doc.route)
    else:
        print("FAILURE: Route not generated or incorrect: " + str(doc.route))
        
    # Cleanup
    doc.delete()

if __name__ == "__main__":
    try:
        test_route_fix()
    except Exception as e:
        print(f"ERROR: {e}")
