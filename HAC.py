import os
from playwright.sync_api import sync_playwright

HAC_URL = "https://homeaccess.katyisd.org/HomeAccess/"
HAC_USER = os.getenv("HAC_USERNAME")
HAC_PASS = os.getenv("HAC_PASSWORD")

def get_hac_grades():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            base_url = "https://homeaccess.katyisd.org/HomeAccess"

            # 1. Login to Katy ISD HAC
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

            # 2. Click the 'Grades' tab
            grades_tab = page.locator('a:has-text("Grades"), #hac-Grades, [title="Grades"]').first
            if grades_tab.count() > 0:
                grades_tab.click()
                page.wait_for_load_state("networkidle")

            # 3. Scan all frames for page content
            page.wait_for_timeout(3000)  # Short pause for ASP.NET dynamic panel render
            
            frames_to_check = page.frames if len(page.frames) > 1 else [page]
            grades_summary = []

            for frame in frames_to_check:
                # Look for course headers or table rows
                headings = frame.locator(".sg-header-heading, .sg-asp-table-data-row, [class*='header']").all()
                for h in headings:
                    text = h.inner_text().strip()
                    # Filter for Katy ISD course code pattern (e.g. 0113A - 6 APENGLAN A)
                    if text and any(code in text for code in ["AP", "KAP", "ENG", "PRE CALC", "CALC", "PHYSICS", "COMP SCI", "BAND", "MUS"]):
                        # Clean multiple newlines into a single string
                        clean_text = " ".join(text.split())
                        grades_summary.append(f"• {clean_text}")

            browser.close()

            if not grades_summary:
                return "No class grade elements found on the page."

            return "Current Class Averages:\n" + "\n".join(grades_summary)

    except Exception as e:
        return f"Error fetching HAC grades: {e}"

if __name__ == "__main__":
    print(get_hac_grades())