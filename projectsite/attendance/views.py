import csv
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Course, Session, AttendanceRecord, Enrollment, Venue
from .forms import SessionCreateForm


def is_teacher(user):
    return user.is_authenticated and (user.is_staff or user.taught_courses.exists())


def student_checkin_view(request):
    if is_teacher(request.user) and request.GET.get('mode') != 'student':
        return redirect('teacher-dashboard')

    now = timezone.now()
    student_profile = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None

    active_sessions = Session.objects.filter(
        starts_at__lte=now, ends_at__gte=now
    ).select_related('course', 'venue')

    if student_profile:
        active_sessions = active_sessions.filter(course__enrollments__student=student_profile)

    upcoming_sessions = Session.objects.filter(
        starts_at__gt=now
    ).select_related('course', 'venue')[:5]

    return render(request, 'attendance/student_checkin.html', {
        'active_sessions': active_sessions,
        'upcoming_sessions': upcoming_sessions,
        'student_profile': student_profile,
    })


@login_required
def teacher_dashboard_view(request):
    if not is_teacher(request.user):
        messages.error(request, 'Access denied: Teacher account required.')
        return redirect('student-checkin')

    sessions = Session.objects.select_related('course', 'venue').all()
    if not request.user.is_superuser:
        sessions = sessions.filter(course__teacher=request.user)

    selected_session_id = request.GET.get('session')
    selected_session = None
    records = AttendanceRecord.objects.none()

    if selected_session_id:
        selected_session = sessions.filter(id=selected_session_id).first()
    elif sessions.exists():
        selected_session = sessions.first()

    if selected_session:
        records = AttendanceRecord.objects.filter(session=selected_session).select_related('student')

    checkin_url = request.build_absolute_uri('/?mode=student')

    return render(request, 'attendance/teacher_dashboard.html', {
        'sessions': sessions,
        'selected_session': selected_session,
        'records': records,
        'checkin_url': checkin_url,
    })


@login_required
def export_attendance_csv(request, session_id):
    if not is_teacher(request.user):
        messages.error(request, 'Access denied: Teacher account required.')
        return redirect('student-checkin')

    sessions = Session.objects.select_related('course')
    if not request.user.is_superuser:
        sessions = sessions.filter(course__teacher=request.user)

    session = get_object_or_404(sessions, id=session_id)
    records_by_student = {
        r.student_id: r
        for r in AttendanceRecord.objects.filter(session=session).select_related('student')
    }
    enrollments = Enrollment.objects.filter(course=session.course).select_related('student').order_by('student__lastname', 'student__firstname')

    filename = f"{session.course.code}_{session.starts_at.strftime('%Y%m%d_%H%M')}_attendance.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Last Name', 'First Name', 'Status', 'Distance (m)', 'Latitude', 'Longitude', 'Checked In At'])

    for enrollment in enrollments:
        s = enrollment.student
        rec = records_by_student.get(s.id)
        if rec:
            writer.writerow([
                s.student_id,
                s.lastname,
                s.firstname,
                rec.get_status_display(),
                round(rec.distance_m, 2),
                rec.lat,
                rec.lng,
                timezone.localtime(rec.checked_in_at).strftime('%Y-%m-%d %H:%M:%S'),
            ])
        else:
            writer.writerow([s.student_id, s.lastname, s.firstname, 'Absent', '', '', '', ''])

    return response


@login_required
def session_create_view(request):
    if not is_teacher(request.user):
        messages.error(request, 'Access denied: Teacher account required.')
        return redirect('student-checkin')

    form = SessionCreateForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        session = form.save()
        messages.success(request, f'Session "{session.title}" created and active.')
        return redirect(f'/dashboard/?session={session.id}')

    venues_data = {
        str(v.id): {'lat': v.latitude, 'lng': v.longitude, 'radius': v.default_radius_m}
        for v in Venue.objects.all()
    }
    return render(request, 'attendance/session_create.html', {
        'form': form,
        'venues_data': venues_data,
    })