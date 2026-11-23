import csv
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import (
    AttendanceHolderEditForm,
    AttendanceRecordEditForm,
    CourseEditForm,
    DepartmentEditForm,
    SessionCreateForm,
    SessionEditForm,
    StudentEditForm,
    VenueEditForm,
)
from .models import (
    Department,
    Course,
    Session,
    AttendanceRecord,
    Enrollment,
    Venue,
    Student,
)


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def is_student(user):
    return user.is_authenticated and hasattr(user, "student_profile")


def is_attendance_holder(user):
    return (
        user.is_authenticated
        and not user.is_superuser
        and not hasattr(user, "student_profile")
    )


def redirect_by_role(user):
    if is_admin(user):
        return redirect("admin-dashboard")
    if is_student(user):
        return redirect("student-checkin")
    return redirect("teacher-dashboard")


def unified_login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    selected_role = request.POST.get("role") or request.GET.get("role") or "student"

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request,
                "registration/login.html",
                {
                    "error": "Invalid username or password. Please try again.",
                    "selected_role": selected_role,
                },
            )

        if selected_role == "student" and not is_student(user):
            return render(
                request,
                "registration/login.html",
                {
                    "error": "This account is not registered as a Student.",
                    "selected_role": selected_role,
                },
            )

        if selected_role == "attendance_holder" and not is_attendance_holder(user):
            return render(
                request,
                "registration/login.html",
                {
                    "error": "This account is not registered as an Attendance Holder.",
                    "selected_role": selected_role,
                },
            )

        if selected_role == "admin" and not is_admin(user):
            return render(
                request,
                "registration/login.html",
                {
                    "error": "Access denied: This account does not have Admin privileges.",
                    "selected_role": selected_role,
                },
            )

        login(request, user)
        return redirect_by_role(user)

    return render(
        request,
        "registration/login.html",
        {"selected_role": selected_role},
    )


def student_register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

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
            request, "Student registration successful. You can now sign in."
        )

        return redirect("login")

    return render(request, "registration/student_register.html")


def student_login_view(request):
    return redirect("login")


@login_required
def student_checkin_view(request):
    if not is_student(request.user):
        return redirect_by_role(request.user)

    now = timezone.now()
    student_profile = request.user.student_profile

    active_sessions = Session.objects.filter(
        starts_at__lte=now,
        ends_at__gte=now,
        course__enrollments__student=student_profile,
    ).select_related("course", "venue")

    upcoming_sessions = Session.objects.filter(
        starts_at__gt=now,
        course__enrollments__student=student_profile,
    ).select_related("course", "venue")[:5]

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
    if not is_attendance_holder(request.user):
        messages.error(request, "Access denied: Attendance Holder account required.")
        return redirect_by_role(request.user)

    sessions = Session.objects.select_related("course", "venue").filter(
        course__teacher=request.user
    )

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

    checkin_url = request.build_absolute_uri("/")

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
    if not is_attendance_holder(request.user):
        messages.error(request, "Access denied: Attendance Holder account required.")
        return redirect_by_role(request.user)

    sessions = Session.objects.select_related("course").filter(
        course__teacher=request.user
    )
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
    if not is_attendance_holder(request.user):
        messages.error(request, "Access denied: Attendance Holder account required.")
        return redirect_by_role(request.user)

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
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

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
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

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

        messages.success(request, "Attendance Holder account created successfully.")
        return redirect("admin-dashboard")

    return render(request, "admin/teacher_form.html")


@login_required
def admin_department_create_view(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

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

        Department.objects.create(code=code, name=name)
        messages.success(request, "Department created successfully.")
        return redirect("admin-dashboard")

    return render(request, "admin/department_form.html")


@login_required
def admin_course_create_view(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

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


def _edit_model_object(request, model, form_class, pk, item_label, redirect_section):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"{item_label} updated successfully.")
            return redirect(f"/admin-dashboard/?section={redirect_section}")
    else:
        form = form_class(instance=obj)

    return render(
        request,
        "admin/edit_item.html",
        {
            "form": form,
            "item_label": item_label,
            "obj": obj,
            "cancel_section": redirect_section,
        },
    )


def _delete_model_object(
    request, model, pk, item_label, redirect_section, delete_fn=None
):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        if delete_fn:
            delete_fn(obj)
        else:
            obj.delete()
        messages.success(request, f"{item_label} deleted successfully.")
        return redirect(f"/admin-dashboard/?section={redirect_section}")

    return render(
        request,
        "admin/confirm_delete.html",
        {
            "item_label": item_label,
            "obj": obj,
            "cancel_section": redirect_section,
        },
    )


# Students
@login_required
def admin_student_edit_view(request, pk):
    return _edit_model_object(
        request, Student, StudentEditForm, pk, "Student", "students"
    )


@login_required
def admin_student_delete_view(request, pk):
    def _delete_student(student):
        linked_user = student.user
        student.delete()
        if linked_user and not linked_user.is_superuser and not linked_user.is_staff:
            linked_user.delete()

    return _delete_model_object(
        request, Student, pk, "Student", "students", delete_fn=_delete_student
    )


# Attendance Holders
@login_required
def admin_teacher_edit_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

    teacher = get_object_or_404(
        User.objects.filter(is_staff=False, is_superuser=False).exclude(
            student_profile__isnull=False
        ),
        pk=pk,
    )
    if request.method == "POST":
        form = AttendanceHolderEditForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance Holder updated successfully.")
            return redirect("/admin-dashboard/?section=teachers")
    else:
        form = AttendanceHolderEditForm(instance=teacher)

    return render(
        request,
        "admin/edit_item.html",
        {
            "form": form,
            "item_label": "Attendance Holder",
            "obj": teacher,
            "cancel_section": "teachers",
        },
    )


@login_required
def admin_teacher_delete_view(request, pk):
    teacher_qs = User.objects.filter(is_staff=False, is_superuser=False).exclude(
        student_profile__isnull=False
    )
    if not is_admin(request.user):
        messages.error(request, "Access denied: Administrator account required.")
        return redirect_by_role(request.user)

    teacher = get_object_or_404(teacher_qs, pk=pk)
    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Attendance Holder deleted successfully.")
        return redirect("/admin-dashboard/?section=teachers")

    return render(
        request,
        "admin/confirm_delete.html",
        {
            "item_label": "Attendance Holder",
            "obj": teacher,
            "cancel_section": "teachers",
        },
    )


# Courses
@login_required
def admin_course_edit_view(request, pk):
    return _edit_model_object(
        request, Course, CourseEditForm, pk, "Course", "courses"
    )


@login_required
def admin_course_delete_view(request, pk):
    return _delete_model_object(request, Course, pk, "Course", "courses")


# Departments
@login_required
def admin_department_edit_view(request, pk):
    return _edit_model_object(
        request, Department, DepartmentEditForm, pk, "Department", "departments"
    )


@login_required
def admin_department_delete_view(request, pk):
    return _delete_model_object(
        request, Department, pk, "Department", "departments"
    )


# Venues
@login_required
def admin_venue_edit_view(request, pk):
    return _edit_model_object(
        request, Venue, VenueEditForm, pk, "Venue", "venues"
    )


@login_required
def admin_venue_delete_view(request, pk):
    return _delete_model_object(request, Venue, pk, "Venue", "venues")


# Sessions
@login_required
def admin_session_edit_view(request, pk):
    return _edit_model_object(
        request, Session, SessionEditForm, pk, "Session", "sessions"
    )


@login_required
def admin_session_delete_view(request, pk):
    return _delete_model_object(request, Session, pk, "Session", "sessions")


# Attendance Records
@login_required
def admin_attendance_edit_view(request, pk):
    return _edit_model_object(
        request,
        AttendanceRecord,
        AttendanceRecordEditForm,
        pk,
        "Attendance Record",
        "attendance",
    )


@login_required
def admin_attendance_delete_view(request, pk):
    return _delete_model_object(
        request, AttendanceRecord, pk, "Attendance Record", "attendance"
    )