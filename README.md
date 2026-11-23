# GeoAttend

account for admin(so Maam can access the system):
Username: GeoAttend
pass: 12345678

GeoAttend is a web-based attendance system we built using Django. Instead of waiting a long line to get attendace, students can check in using their phones or laptops, and the system checks if they are actually inside the range or venue using GPS location.

## What It Does
- **Location Check (Geofencing):** Makes sure students are within the allowed distance (radius) of the class venue before marking them present.
- **Three User Roles:** Has separate dashboards for Students, Attendance Holders, and Admins on one login page.
- **Easy Record Tracking:** Attendance Holders can create class sessions and see who checked in, while Admins can manage users, courses, departments, and venues.

## How the System Works (Flow)

1. **Admin Setup**
   - The Admin logs in and sets up the academic departments, courses, venues (with GPS coordinates and radius), and creates accounts for Attendance Holders.

2. **Student Registration & Login**
   - Students register an account using their Student ID and details, or log in through the unified login page by picking their role (`Student`, `Attendance Holder`, or `Admin`).

3. **Creating a Session**
   - The Attendance Holder logs into their dashboard, selects their course and venue, sets the start and end time, and starts an attendance session.

4. **Student Check-In**
   - The student opens the active session on their dashboard and allows browser GPS access.
   - GeoAttend calculates the distance between the student's current location and the venue pin.
   - If the student is inside the allowed radius and within the session time, their attendance is recorded as **Present** (or **Late** depending on the time). If they are too far away, the check-in is blocked.

5. **Viewing Records**
   - Both the Attendance Holder and Admin can view the attendance logs, distances, and check-in timestamps anytime.

## TEAM
- Delos Santos, Dariel Jean
- Alapad, Reynald
- Gulane, Trizthan
- Grande, Brix
