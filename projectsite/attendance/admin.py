from django.contrib import admin
from .models import (
    Department, Course, Student, Enrollment,
    Venue, Session, AttendanceRecord
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at')
    search_fields = ('code', 'name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'teacher')
    list_filter = ('department',)
    search_fields = ('code', 'name', 'teacher__username')
    list_select_related = ('department', 'teacher')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'lastname', 'firstname', 'email', 'user')
    search_fields = ('student_id', 'lastname', 'firstname', 'email')
    list_select_related = ('user',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)
    search_fields = ('student__student_id', 'student__lastname', 'course__code')
    list_select_related = ('student', 'course')


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'default_radius_m')
    search_fields = ('name',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'venue', 'radius_m', 'starts_at', 'ends_at')
    list_filter = ('course', 'venue')
    search_fields = ('title', 'course__code')
    list_select_related = ('course', 'venue')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'distance_m', 'checked_in_at')
    list_filter = ('status', 'session__course')
    search_fields = ('student__student_id', 'student__lastname', 'session__title')
    list_select_related = ('student', 'session')