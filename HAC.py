import os
from playwright.sync_api import sync_playwright

HAC_URL = "https://homeaccess.katyisd.org/HomeAccess/"
HAC_USER = os.getenv("HAC_USERNAME")
HAC_PASS = os.getenv("HAC_PASSWORD")

def get_hac_grades():
    if not HAC_USER or not HAC_PASS:
        return "HAC credentials not set in environment variables."

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to login page
            page.goto(HAC_URL)

            # Fill credentials and submit (adjust selectors if Katy ISD uses custom SSO)
            page.fill("#LogOnDetails_UserName", HAC_USER)
            page.fill("#LogOnDetails_Password", HAC_PASS)
            page.click("#btnLogin")

            # Navigate to Classes / Grades tab
            page.goto("https://homeaccess.katyisd.org/HomeAccess/Content/Student/Assignments.aspx")

            # Extract grade text/tables from the page
            # Note: CSS selectors will depend on the exact HAC page layout
            grades_data = page.inner_text("#MainContent")

            browser.close()
            return grades_data

        except Exception as e:
            browser.close()
            return f"Error fetching HAC grades: {e}"

if __name__ == "__main__":
    print(get_hac_grades())