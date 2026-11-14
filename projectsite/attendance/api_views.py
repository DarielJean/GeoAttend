from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
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
    permission_classes = [IsAdminUser]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department', 'teacher').all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminUser]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('user').all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminUser]


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related('student', 'course').all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminUser]


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    permission_classes = [IsAdminUser]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related('course', 'venue').all()
    serializer_class = SessionSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'], url_path='checkin', permission_classes=[AllowAny])
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

        if request.user.is_authenticated and getattr(request.user, 'student_profile', None):
            student = request.user.student_profile
            student_id = student.student_id
        else:
            student_id = serializer.validated_data['student_id']
            student = get_object_or_404(Student, student_id=student_id)

        if not Enrollment.objects.filter(student=student, course=session.course).exists():
            return Response(
                {'detail': f'Student {student_id} is not enrolled in {session.course.code}.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if AttendanceRecord.objects.filter(session=session, student=student).exists():
            return Response(
                {'detail': 'Attendance has already been recorded for this session.'},
                status=status.HTTP_409_CONFLICT
            )

        device_id = serializer.validated_data.get('device_id', '').strip()
        if device_id and AttendanceRecord.objects.filter(session=session, device_id=device_id).exclude(student=student).exists():
            return Response(
                {'detail': 'This device has already been used to check in another student for this session.'},
                status=status.HTTP_403_FORBIDDEN
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
            device_id=device_id,
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
    permission_classes = [IsAdminUser]