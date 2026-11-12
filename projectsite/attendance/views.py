from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Session, AttendanceRecord, Venue
from .forms import SessionCreateForm


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


def session_create_view(request):
    if request.method == 'POST':
        form = SessionCreateForm(request.POST)
        if form.is_valid():
            session = form.save()
            return redirect(f"/dashboard/?session={session.id}")
    else:
        form = SessionCreateForm(initial={
            'center_lat': 9.776400,
            'center_lng': 118.734000,
            'radius_m': 50,
        })

    venues_data = {
        str(v.id): {
            'lat': v.latitude,
            'lng': v.longitude,
            'radius': v.default_radius_m,
        }
        for v in Venue.objects.all()
    }

    return render(request, 'attendance/session_create.html', {
        'form': form,
        'venues_data': venues_data,
    })