from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Department(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(BaseModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code}: {self.name}"


class Student(BaseModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ['lastname', 'firstname']

    def __str__(self):
        return f"{self.student_id} - {self.lastname}, {self.firstname}"


class Enrollment(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.student_id} -> {self.course.code}"


class Venue(BaseModel):
    name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    default_radius_m = models.PositiveIntegerField(default=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.default_radius_m}m)"


class Session(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    title = models.CharField(max_length=200)
    center_lat = models.FloatField()
    center_lng = models.FloatField()
    radius_m = models.PositiveIntegerField(default=50)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    late_after = models.DateTimeField()

    class Meta:
        ordering = ['-starts_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class AttendanceRecord(BaseModel):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('rejected', 'Rejected'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    lat = models.FloatField()
    lng = models.FloatField()
    distance_m = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    device_id = models.CharField(max_length=64, blank=True, default='')
    checked_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['-checked_in_at']

    def __str__(self):
        return f"{self.student.student_id} | {self.session.title} ({self.status})"