from rest_framework import serializers
from .models import (
    Department, Course, Student, Enrollment,
    Venue, Session, AttendanceRecord
)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    department_code = serializers.CharField(source='department.code', read_only=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    student_id_number = serializers.CharField(source='student.student_id', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    venue_name = serializers.CharField(source='venue.name', read_only=True)

    class Meta:
        model = Session
        fields = '__all__'


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_id_number = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    session_title = serializers.CharField(source='session.title', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ('distance_m', 'status', 'checked_in_at')

    def get_student_name(self, obj):
        return f"{obj.student.lastname}, {obj.student.firstname}"


class CheckInRequestSerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=50)
    lat = serializers.FloatField(min_value=-90.0, max_value=90.0)
    lng = serializers.FloatField(min_value=-180.0, max_value=180.0)
    accuracy_m = serializers.FloatField(required=False)
    device_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')

    def validate_accuracy_m(self, value):
        if value > 150:
            raise serializers.ValidationError(
                f"GPS signal accuracy too weak (±{int(value)}m). Move near a window or enable precise device location."
            )
        return value

accuracy_m = serializers.FloatField(required=False, default=0)

def validate_accuracy_m(self, value):
    if value > 150:
        raise serializers.ValidationError(
            f"GPS signal accuracy too weak (±{int(value)}m). Move near a window or enable precise device location."
        )
    return value