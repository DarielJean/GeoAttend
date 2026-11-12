from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Department, Course, Student, Enrollment,
    Venue, Session, AttendanceRecord
)
from .serializers import (
    DepartmentSerializer, CourseSerializer, StudentSerializer,
    EnrollmentSerializer, VenueSerializer, SessionSerializer,
    AttendanceRecordSerializer, CheckInRequestSerializer
)
from .services import calculate_haversine_distance, evaluate_checkin_status


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department', 'teacher').all()
    serializer_class = CourseSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('user').all()
    serializer_class = StudentSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related('student', 'course').all()
    serializer_class = EnrollmentSerializer


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related('course', 'venue').all()
    serializer_class = SessionSerializer

    @action(detail=True, methods=['post'], url_path='checkin')
    def checkin(self, request, pk=None):
        session = self.get_object()
        serializer = CheckInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        now = timezone.now()
        if now < session.starts_at:
            return Response(
                {'detail': 'This attendance session has not started yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if now > session.ends_at:
            return Response(
                {'detail': 'This attendance session has already closed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_id = serializer.validated_data['student_id']
        student = get_object_or_404(Student, student_id=student_id)

        # Verify student is enrolled in the session's course
        if not Enrollment.objects.filter(student=student, course=session.course).exists():
            return Response(
                {'detail': f'Student {student_id} is not enrolled in {session.course.code}.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent duplicate check-ins for the same session
        if AttendanceRecord.objects.filter(session=session, student=student).exists():
            return Response(
                {'detail': 'Attendance has already been recorded for this session.'},
                status=status.HTTP_409_CONFLICT
            )

        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        distance_m = calculate_haversine_distance(
            session.center_lat, session.center_lng, lat, lng
        )
        checkin_status = evaluate_checkin_status(session, distance_m, now)

        record = AttendanceRecord.objects.create(
            session=session,
            student=student,
            lat=lat,
            lng=lng,
            distance_m=distance_m,
            status=checkin_status,
        )

        response_data = AttendanceRecordSerializer(record).data
        http_status = (
            status.HTTP_201_CREATED
            if checkin_status in ('present', 'late')
            else status.HTTP_403_FORBIDDEN
        )
        return Response(response_data, status=http_status)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('session', 'student').all()
    serializer_class = AttendanceRecordSerializer