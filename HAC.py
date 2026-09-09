import os
from playwright.sync_api import sync_playwright

HAC_URL = "https://homeaccess.katyisd.org/HomeAccess/"
HAC_USER = os.getenv("HAC_USERNAME")
HAC_PASS = os.getenv("HAC_PASSWORD")

def get_hac_grades():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            base_url = "https://homeaccess.katyisd.org/HomeAccess"

            # 1. Login
            page.goto(f"{base_url}/Account/LogOn", wait_until="networkidle")
            page.wait_for_selector('input[name="LogOnDetails.UserName"]', timeout=10000)
            
            page.fill('input[name="LogOnDetails.UserName"]', HAC_USER)
            page.fill('input[name="LogOnDetails.Password"]', HAC_PASS)

            login_button = page.locator('button[type="submit"], input[type="submit"], #btnLogin').first
            login_button.click()
            page.wait_for_load_state("networkidle")

            if "Your attempt to log in was unsuccessful" in page.inner_text("body"):
                browser.close()
                return "Error: Invalid HAC username or password."

            # 2. Navigate directly to Classes / Classwork tab (Live Grades)
            page.goto(f"{base_url}/Content/Student/Assignments.aspx", wait_until="networkidle")
            page.wait_for_timeout(3000)

            # Locate active iframe if present
            target_frame = page
            for frame in page.frames:
                if frame.locator(".AssignmentClass, .sg-asp-table").count() > 0:
                    target_frame = frame
                    break

            output_lines = ["=== CURRENT LIVE GRADES & ASSIGNMENTS ==="]
            
            # Locate all course assignment blocks
            courses = target_frame.locator(".AssignmentClass").all()
            
            if not courses:
                # Fallback: Parse whole body inner text if structure changes
                body_text = target_frame.inner_text("body")
                browser.close()
                return f"=== RAW CLASSWORK TEXT ===\n{body_text}"

            for course in courses:
                # Course Header contains Title + Current Running Average (e.g., '1010 - ENG 1 (94.50%)')
                header_elem = course.locator(".sg-header-heading, .CourseHeader, .AssignmentGroupHeaderRow").first
                header_text = " ".join(header_elem.inner_text().split()) if header_elem.count() > 0 else "Unknown Class"
                
                output_lines.append(f"\nCourse: {header_text}")
                output_lines.append("Assignments:")

                # Get all individual assignment rows for this specific class
                assignments = course.locator(".sg-asp-table-data-row").all()
                for assignment in assignments:
                    assign_text = " ".join(assignment.inner_text().split())
                    if assign_text:
                        output_lines.append(f"  - {assign_text}")

            browser.close()
            return "\n".join(output_lines)

    except Exception as e:
        return f"Error fetching HAC grades: {e}"

if __name__ == "__main__":
    print(get_hac_grades())