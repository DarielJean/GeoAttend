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
]
