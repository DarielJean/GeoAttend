import csv
import json
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import SessionCreateForm

from .models import (
    Department,
    Course,
    Session,
    AttendanceRecord,
    Enrollment,
    Venue,
    Student,
)


def is_teacher(user):
    return user.is_authenticated and (user.is_staff or user.taught_courses.exists())


def student_register_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "student_profile"):
            return redirect("student-checkin")
        return redirect("teacher-dashboard")

    if request.method == "POST":
        student_id = request.POST.get("student_id", "").strip()
        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not all(
            [student_id, firstname, lastname, email, password, confirm_password]
        ):
            return render(
                request,
                "registration/student_register.html",
                {"error": "Please fill in all fields."},
            )

        if password != confirm_password:
            return render(
                request,
                "registration/student_register.html",
                {"error": "Passwords do not match."},
            )

        if len(password) < 6:
            return render(
                request,
                "registration/student_register.html",
                {"error": "Password must be at least 6 characters."},
            )

        if Student.objects.filter(student_id=student_id).exists():
            return render(
                request,
                "registration/student_register.html",
                {"error": "Student ID is already registered."},
            )

        if Student.objects.filter(email=email).exists():
            return render(
                request,
                "registration/student_register.html",
                {"error": "Email is already registered."},
            )

        if User.objects.filter(username=student_id).exists():
            return render(
                request,
                "registration/student_register.html",
                {"error": "This Student ID already has an account."},
            )

        user = User.objects.create_user(
            username=student_id,
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
        )

        Student.objects.create(
            user=user,
            student_id=student_id,
            firstname=firstname,
            lastname=lastname,
            email=email,
        )

        messages.success(
            request, "Student registration successful. You can now log in."
        )

        return redirect("student-login")

    return render(request, "registration/student_register.html")


def student_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "student_profile"):
            return redirect("student-checkin")
        return redirect("teacher-dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None and hasattr(user, "student_profile"):
            login(request, user)
            return redirect("student-checkin")

        return render(
            request,
            "registration/student_login.html",
            {"error": "Invalid student username or password."},
        )

    return render(request, "registration/student_login.html")


@login_required
def student_checkin_view(request):
    if is_teacher(request.user) and request.GET.get("mode") != "student":
        return redirect("teacher-dashboard")

    now = timezone.now()

    student_profile = (
        getattr(request.user, "student_profile", None)
        if request.user.is_authenticated
        else None
    )

    active_sessions = Session.objects.filter(
        starts_at__lte=now, ends_at__gte=now
    ).select_related("course", "venue")

    if student_profile:
        active_sessions = active_sessions.filter(
            course__enrollments__student=student_profile
        )

    upcoming_sessions = Session.objects.filter(starts_at__gt=now).select_related(
        "course", "venue"
    )[:5]

    return render(
        request,
        "attendance/student_checkin.html",
        {
            "active_sessions": active_sessions,
            "upcoming_sessions": upcoming_sessions,
            "student_profile": student_profile,
        },
    )


@login_required
def teacher_dashboard_view(request):
    if not is_teacher(request.user):
        messages.error(request, "Access denied: Teacher account required.")
        return redirect("student-checkin")

    sessions = Session.objects.select_related("course", "venue").all()

    if not request.user.is_superuser:
        sessions = sessions.filter(course__teacher=request.user)

    selected_session_id = request.GET.get("session")
    selected_session = None
    records = AttendanceRecord.objects.none()

    if selected_session_id:
        selected_session = sessions.filter(id=selected_session_id).first()
    elif sessions.exists():
        selected_session = sessions.first()

    if selected_session:
        records = AttendanceRecord.objects.filter(
            session=selected_session
        ).select_related("student")

    checkin_url = request.build_absolute_uri("/?mode=student")

    return render(
        request,
        "attendance/teacher_dashboard.html",
        {
            "sessions": sessions,
            "selected_session": selected_session,
            "records": records,
            "checkin_url": checkin_url,
        },
    )


@login_required
def export_attendance_csv(request, session_id):
    if not is_teacher(request.user):
        messages.error(request, "Access denied: Teacher account required.")
        return redirect("student-checkin")

    sessions = Session.objects.select_related("course")

    if not request.user.is_superuser:
        sessions = sessions.filter(course__teacher=request.user)

    session = get_object_or_404(sessions, id=session_id)

    records_by_student = {
        r.student_id: r
        for r in AttendanceRecord.objects.filter(session=session).select_related(
            "student"
        )
    }

    enrollments = (
        Enrollment.objects.filter(course=session.course)
        .select_related("student")
        .order_by("student__lastname", "student__firstname")
    )

    filename = (
        f"{session.course.code}_"
        f"{session.starts_at.strftime('%Y%m%d_%H%M')}_"
        f"attendance.csv"
    )

    response = HttpResponse(content_type="text/csv")

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    writer.writerow(
        [
            "Student ID",
            "Last Name",
            "First Name",
            "Status",
            "Distance (m)",
            "Latitude",
            "Longitude",
            "Checked In At",
        ]
    )

    for enrollment in enrollments:
        s = enrollment.student
        rec = records_by_student.get(s.id)

        if rec:
            writer.writerow(
                [
                    s.student_id,
                    s.lastname,
                    s.firstname,
                    rec.get_status_display(),
                    round(rec.distance_m, 2),
                    rec.lat,
                    rec.lng,
                    timezone.localtime(rec.checked_in_at).strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )
        else:
            writer.writerow(
                [
                    s.student_id,
                    s.lastname,
                    s.firstname,
                    "Absent",
                    "",
                    "",
                    "",
                    "",
                ]
            )

    return response


@login_required
def session_create_view(request):
    if not is_teacher(request.user):
        messages.error(request, "Access denied: Teacher account required.")
        return redirect("student-checkin")

    form = SessionCreateForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        session = form.save()

        messages.success(request, f'Session "{session.title}" created and active.')

        return redirect(f"/dashboard/?session={session.id}")

    venues_data = {
        str(v.id): {
            "lat": v.latitude,
            "lng": v.longitude,
            "radius": v.default_radius_m,
        }
        for v in Venue.objects.all()
    }

    return render(
        request,
        "attendance/session_create.html",
        {
            "form": form,
            "venues_data": venues_data,
        },
    )


@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Administrator account required.")
        return redirect("student-checkin")

    students = Student.objects.all().select_related("user")
    courses = Course.objects.all().select_related("department", "teacher")
    sessions = Session.objects.all().select_related("course", "venue")
    venues = Venue.objects.all()
    departments = Department.objects.all()
    attendance_records = AttendanceRecord.objects.all().select_related(
        "student",
        "session",
        "session__course",
    )

    teachers = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    ).exclude(student_profile__isnull=False)

    return render(
        request,
        "admin/admin_dashboard.html",
        {
            "students": students,
            "courses": courses,
            "sessions": sessions,
            "venues": venues,
            "departments": departments,
            "attendance_records": attendance_records,
            "teachers": teachers,
        },
    )


@login_required
def admin_teacher_create_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Administrator account required.")
        return redirect("student-checkin")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not all([username, firstname, lastname, email, password]):
            return render(
                request,
                "admin/teacher_form.html",
                {"error": "Please fill in all fields."},
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "admin/teacher_form.html",
                {"error": "Username is already taken."},
            )

        if User.objects.filter(email=email).exists():
            return render(
                request,
                "admin/teacher_form.html",
                {"error": "Email is already registered."},
            )

        User.objects.create_user(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email,
            password=password,
        )

        messages.success(request, "Teacher account created successfully.")

        return redirect("admin-dashboard")

    return render(request, "admin/teacher_form.html")


@login_required
def admin_department_create_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Administrator account required.")
        return redirect("student-checkin")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()

        if not code or not name:
            return render(
                request,
                "admin/department_form.html",
                {"error": "Please fill in all fields."},
            )

        if Department.objects.filter(code=code).exists():
            return render(
                request,
                "admin/department_form.html",
                {"error": "Department code already exists."},
            )

        if Department.objects.filter(name=name).exists():
            return render(
                request,
                "admin/department_form.html",
                {"error": "Department name already exists."},
            )

        Department.objects.create(
            code=code,
            name=name,
        )

        messages.success(request, "Department created successfully.")

        return redirect("admin-dashboard")

    return render(request, "admin/department_form.html")


@login_required
def admin_course_create_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied: Administrator account required.")
        return redirect("student-checkin")

    departments = Department.objects.all()
    teachers = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    ).exclude(student_profile__isnull=False)

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        department_id = request.POST.get("department")
        teacher_id = request.POST.get("teacher")

        if not all([code, name, department_id, teacher_id]):
            return render(
                request,
                "admin/course_form.html",
                {
                    "error": "Please fill in all fields.",
                    "departments": departments,
                    "teachers": teachers,
                },
            )

        if Course.objects.filter(code=code).exists():
            return render(
                request,
                "admin/course_form.html",
                {
                    "error": "Course code already exists.",
                    "departments": departments,
                    "teachers": teachers,
                },
            )

        department = get_object_or_404(Department, id=department_id)
        teacher = get_object_or_404(User, id=teacher_id)

        Course.objects.create(
            code=code,
            name=name,
            department=department,
            teacher=teacher,
        )

        messages.success(request, "Course created successfully.")

        return redirect("admin-dashboard")

    return render(
        request,
        "admin/course_form.html",
        {
            "departments": departments,
            "teachers": teachers,
        },
    )
