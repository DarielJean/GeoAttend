from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    DepartmentViewSet, CourseViewSet, StudentViewSet,
    EnrollmentViewSet, VenueViewSet, SessionViewSet,
    AttendanceRecordViewSet
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'students', StudentViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'venues', VenueViewSet)
router.register(r'sessions', SessionViewSet)
router.register(r'attendance-records', AttendanceRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]