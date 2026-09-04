from canvasapi import Canvas
from datetime import datetime, timedelta
import requests
import os

API_URL="https://katyisd.instructure.com/"
API_KEY=os.getenv("CANVAS_TOKEN")

def get_canvas_data():
    # Initialize the Canvas API object
    canvas = Canvas(API_URL, API_KEY)
    
    # Get current authenticated user
    user = canvas.get_current_user()
    print(f"Authenticated as: {user.name} (ID: {user.id})\n")

    # -------------------------------------------------------------
    # 1. Access Active Courses
    # -------------------------------------------------------------
    print("=== COURSES ===")
    # enrollment_state='active' ensures old ended courses aren't returned
    courses = user.get_courses(enrollment_state='active')
    
    active_courses = []
    for course in courses:
        # Ignore untitled or placeholder courses
        if hasattr(course, 'name'):
            print(f"Course ID: {course.id} | Name: {course.name}")
            active_courses.append(course)

    # -------------------------------------------------------------
    # 2. Access Assignments for Each Course
    # -------------------------------------------------------------
    print("\n=== ASSIGNMENTS PER COURSE ===")
    for course in active_courses:
        print(f"\n--- {course.name} ---")
        try:
            assignments = course.get_assignments()
            has_assignments = False
            for assignment in assignments:
                has_assignments = True
                due_date = getattr(assignment, 'due_at', 'No due date')
                print(f"  • [{assignment.id}] {assignment.name} (Due: {due_date})")
            
            if not has_assignments:
                print("  (No assignments found)")
        except Exception as e:
            print(f"  Could not fetch assignments: {e}")

    # -------------------------------------------------------------
    # 3. Access Calendar Events
    # -------------------------------------------------------------
    print("\n=== UPCOMING CALENDAR EVENTS (Next 30 Days) ===")
    
    # Set date range for calendar query
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    # Context codes specify which calendars to pull from (user and enrolled courses)
    context_codes = [f"user_{user.id}"] + [f"course_{c.id}" for c in active_courses]

    calendar_events = canvas.get_calendar_events(
        type='event',
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        context_codes=context_codes
    )

    events_found = False
    for event in calendar_events:
        events_found = True
        event_time = getattr(event, 'start_at', 'All Day / Unspecified')
        print(f"  • {event.title} (Date: {event_time})")

    if not events_found:
        print("  No calendar events scheduled in the next 30 days.")

def get_user_schedule_summary():
    canvas = Canvas(API_URL, API_KEY)
    user = canvas.get_current_user()
    courses = user.get_courses(enrollment_state='active')
    
    summary = []
    for course in courses:
        if hasattr(course, 'name'):
            summary.append(f"Course: {course.name}")
            for assignment in course.get_assignments():
                summary.append(f"  - Assignment: {assignment.name}, Due: {getattr(assignment, 'due_at', 'None')}")
                
    return "\n".join(summary)

if __name__ == "__main__":
    get_canvas_data()
