from canvasapi import Canvas
from datetime import datetime, timedelta, timezone
import os

API_URL = "https://katyisd.instructure.com/"
#API_KEY = os.getenv("CANVAS_TOKEN")
API_KEY = "2174~7fKWKVvHmZuP6EKaXAkxB237T9eX4KWvNWEHWfvWU8cLw4NT3u4UzauVA462x6my"

def get_canvas_data():
    canvas = Canvas(API_URL, API_KEY)
    user = canvas.get_current_user()
    print(f"Authenticated as: {user.name} (ID: {user.id})\n")

    # Time frame: Now to 14 days in the future
    now = datetime.now(timezone.utc)
    two_weeks_from_now = now + timedelta(days=14)

    # 1. Fetch Active Courses & Assignments
    print("=== COURSES & UPCOMING ASSIGNMENTS (NEXT 2 WEEKS) ===")
    courses = user.get_courses(enrollment_state='active')
    active_courses = []
    
    for course in courses:
        if not hasattr(course, 'name'):
            continue
            
        active_courses.append(course)
        print(f"\nCourse: {course.name} (ID: {course.id})")
        
        try:
            assignments = course.get_assignments()
            upcoming_found = False
            
            for assignment in assignments:
                due_at_str = getattr(assignment, 'due_at', None)
                if not due_at_str:
                    continue

                due_date = datetime.fromisoformat(due_at_str.replace("Z", "+00:00"))

                # Filter: Only show if due between today and 2 weeks out
                if now <= due_date <= two_weeks_from_now:
                    upcoming_found = True
                    formatted_due = due_date.strftime("%b %d, %Y at %I:%M %p UTC")
                    print(f"  • [{assignment.id}] {assignment.name} — Due: {formatted_due}")

            if not upcoming_found:
                print("  (No assignments due in the next 2 weeks)")

        except Exception as e:
            print(f"  Could not fetch assignments: {e}")

    # 2. Fetch Calendar Events (Next 2 Weeks)
    print("\n=== UPCOMING CALENDAR EVENTS (NEXT 2 WEEKS) ===")
    context_codes = [f"user_{user.id}"] + [f"course_{c.id}" for c in active_courses]

    try:
        calendar_events = canvas.get_calendar_events(
            type='event',
            start_date=now.strftime("%Y-%m-%d"),
            end_date=two_weeks_from_now.strftime("%Y-%m-%d"),
            context_codes=context_codes
        )

        events_found = False
        for event in calendar_events:
            events_found = True
            event_time = getattr(event, 'start_at', None)
            if event_time:
                event_date = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
                formatted_time = event_date.strftime("%b %d, %Y at %I:%M %p UTC")
            else:
                formatted_time = "All Day / Unspecified"

            print(f"  • {event.title} — Date: {formatted_time}")

        if not events_found:
            print("  No calendar events scheduled in the next 2 weeks.")

    except Exception as e:
        print(f"  Could not fetch calendar events: {e}")

def get_user_schedule_summary():
    """Formats the 2-week schedule (assignments + calendar events) for R2D2."""
    canvas = Canvas(API_URL, API_KEY)
    user = canvas.get_current_user()
    courses = user.get_courses(enrollment_state='active')
    
    now = datetime.now(timezone.utc)
    two_weeks_from_now = now + timedelta(days=14)
    
    summary = []
    active_courses = []
    
    # Assignments
    for course in courses:
        if not hasattr(course, 'name'):
            continue
            
        active_courses.append(course)
        course_has_items = False
        course_lines = [f"Course: {course.name}"]
        
        try:
            for assignment in course.get_assignments():
                due_at_str = getattr(assignment, 'due_at', None)
                if not due_at_str:
                    continue

                due_date = datetime.fromisoformat(due_at_str.replace("Z", "+00:00"))

                if now <= due_date <= two_weeks_from_now:
                    course_has_items = True
                    formatted_due = due_date.strftime("%b %d at %I:%M %p UTC")
                    course_lines.append(f"  - Assignment: {assignment.name}, Due: {formatted_due}")

            if course_has_items:
                summary.extend(course_lines)
        except Exception:
            continue

    # Calendar Events
    context_codes = [f"user_{user.id}"] + [f"course_{c.id}" for c in active_courses]
    try:
        calendar_events = canvas.get_calendar_events(
            type='event',
            start_date=now.strftime("%Y-%m-%d"),
            end_date=two_weeks_from_now.strftime("%Y-%m-%d"),
            context_codes=context_codes
        )
        
        event_lines = ["\nCalendar Events:"]
        has_events = False
        for event in calendar_events:
            has_events = True
            event_lines.append(f"  - Event: {event.title}")
            
        if has_events:
            summary.extend(event_lines)
    except Exception:
        pass

    if not summary:
        return "No assignments or events scheduled in the next 2 weeks."
        
    return "\n".join(summary)

if __name__ == "__main__":
    get_canvas_data()