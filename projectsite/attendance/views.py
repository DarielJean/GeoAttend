from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Session, AttendanceRecord


def student_checkin_view(request):
    now = timezone.now()
    active_sessions = Session.objects.select_related('course', 'venue').filter(
        starts_at__lte=now,
        ends_at__gte=now
    )
    upcoming_sessions = Session.objects.select_related('course', 'venue').filter(
        starts_at__gt=now
    )[:5]

    return render(request, 'attendance/student_checkin.html', {
        'active_sessions': active_sessions,
        'upcoming_sessions': upcoming_sessions,
    })


def teacher_dashboard_view(request):
    sessions = Session.objects.select_related('course', 'venue').all()
    selected_session_id = request.GET.get('session')

    if selected_session_id:
        selected_session = get_object_or_404(Session, id=selected_session_id)
    else:
        selected_session = sessions.first()

    records = []
    if selected_session:
        records = AttendanceRecord.objects.select_related('student').filter(
            session=selected_session
        )

    return render(request, 'attendance/teacher_dashboard.html', {
        'sessions': sessions,
        'selected_session': selected_session,
        'records': records,
    })