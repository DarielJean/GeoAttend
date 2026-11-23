from django.urls import path
from . import views

urlpatterns = [
    path("student-login/", views.student_login_view, name="student-login"),
    path("student-register/", views.student_register_view, name="student-register"),
    path("", views.student_checkin_view, name="student-checkin"),
    path("dashboard/", views.teacher_dashboard_view, name="teacher-dashboard"),
    path(
        "dashboard/sessions/create/",
        views.session_create_view,
        name="session-create",
    ),
    path(
        "dashboard/sessions/<int:session_id>/export/",
        views.export_attendance_csv,
        name="export-attendance-csv",
    ),
    path("admin-dashboard/", views.admin_dashboard_view, name="admin-dashboard"),
    path(
        "admin-dashboard/teachers/add/",
        views.admin_teacher_create_view,
        name="admin-teacher-create",
    ),
    path(
        "admin-dashboard/departments/add/",
        views.admin_department_create_view,
        name="admin-department-create",
    ),
    path(
        "admin-dashboard/courses/add/",
        views.admin_course_create_view,
        name="admin-course-create",
    ),
    # Students
    path(
        "admin-dashboard/students/<int:pk>/edit/",
        views.admin_student_edit_view,
        name="admin-student-edit",
    ),
    path(
        "admin-dashboard/students/<int:pk>/delete/",
        views.admin_student_delete_view,
        name="admin-student-delete",
    ),
    # Attendance Holders
    path(
        "admin-dashboard/teachers/<int:pk>/edit/",
        views.admin_teacher_edit_view,
        name="admin-teacher-edit",
    ),
    path(
        "admin-dashboard/teachers/<int:pk>/delete/",
        views.admin_teacher_delete_view,
        name="admin-teacher-delete",
    ),
    # Courses
    path(
        "admin-dashboard/courses/<int:pk>/edit/",
        views.admin_course_edit_view,
        name="admin-course-edit",
    ),
    path(
        "admin-dashboard/courses/<int:pk>/delete/",
        views.admin_course_delete_view,
        name="admin-course-delete",
    ),
    # Departments
    path(
        "admin-dashboard/departments/<int:pk>/edit/",
        views.admin_department_edit_view,
        name="admin-department-edit",
    ),
    path(
        "admin-dashboard/departments/<int:pk>/delete/",
        views.admin_department_delete_view,
        name="admin-department-delete",
    ),
    # Venues
    path(
        "admin-dashboard/venues/<int:pk>/edit/",
        views.admin_venue_edit_view,
        name="admin-venue-edit",
    ),
    path(
        "admin-dashboard/venues/<int:pk>/delete/",
        views.admin_venue_delete_view,
        name="admin-venue-delete",
    ),
    # Sessions
    path(
        "admin-dashboard/sessions/<int:pk>/edit/",
        views.admin_session_edit_view,
        name="admin-session-edit",
    ),
    path(
        "admin-dashboard/sessions/<int:pk>/delete/",
        views.admin_session_delete_view,
        name="admin-session-delete",
    ),
    # Attendance Records
    path(
        "admin-dashboard/attendance/<int:pk>/edit/",
        views.admin_attendance_edit_view,
        name="admin-attendance-edit",
    ),
    path(
        "admin-dashboard/attendance/<int:pk>/delete/",
        views.admin_attendance_delete_view,
        name="admin-attendance-delete",
    ),
]