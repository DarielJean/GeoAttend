from django import forms
from django.contrib.auth.models import User
from .models import (
    AttendanceRecord,
    Course,
    Department,
    Session,
    Student,
    Venue,
)


class SessionCreateForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "course",
            "venue",
            "title",
            "center_lat",
            "center_lng",
            "radius_m",
            "starts_at",
            "late_after",
            "ends_at",
        ]
        widgets = {
            "course": forms.Select(attrs={"class": "form-select"}),
            "venue": forms.Select(attrs={"class": "form-select", "id": "venueSelect"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Week 13 - Lecture & Attendance",
                }
            ),
            "center_lat": forms.NumberInput(
                attrs={"class": "form-control", "step": "any", "id": "centerLatInput"}
            ),
            "center_lng": forms.NumberInput(
                attrs={"class": "form-control", "step": "any", "id": "centerLngInput"}
            ),
            "radius_m": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "10",
                    "max": "1000",
                    "id": "radiusInput",
                }
            ),
            "starts_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "late_after": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields["course"].queryset = Course.objects.filter(teacher=user)

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        late_after = cleaned_data.get("late_after")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", "End time must be after the start time.")

        if starts_at and late_after and late_after < starts_at:
            self.add_error(
                "late_after", "Late threshold cannot be earlier than start time."
            )

        if late_after and ends_at and late_after > ends_at:
            self.add_error(
                "late_after", "Late threshold cannot be later than end time."
            )

        return cleaned_data


class StudentEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["student_id", "firstname", "lastname", "email", "user"]


class AttendanceHolderEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]


class CourseEditForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "name", "department", "teacher"]


class DepartmentEditForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["code", "name"]


class VenueEditForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "latitude", "longitude", "default_radius_m"]


class SessionEditForm(SessionCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.all()


class AttendanceRecordEditForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = [
            "session",
            "student",
            "status",
            "distance_m",
            "lat",
            "lng",
            "device_id",
        ]