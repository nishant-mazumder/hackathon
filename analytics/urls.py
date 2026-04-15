from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import auth_views
from . import views

urlpatterns = [
    path("auth/admin/register/", auth_views.AdminRegisterApi.as_view(), name="admin-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", auth_views.AdminMeApi.as_view(), name="auth-me"),
    path("students/", views.StudentListApi.as_view(), name="students-list"),
    path("students/<int:student_id>/", views.StudentProfileApi.as_view(), name="student-profile"),
    path("students/<int:student_id>/grades/trend/", views.GradeTrendApi.as_view(), name="grade-trend"),
    path(
        "students/<int:student_id>/attendance/heatmap/",
        views.AttendanceHeatmapApi.as_view(),
        name="attendance-heatmap",
    ),
    path(
        "students/<int:student_id>/activities/timeline/",
        views.ActivityTimelineApi.as_view(),
        name="activity-timeline",
    ),
    path("students/<int:student_id>/alerts/", views.SmartAlertApi.as_view(), name="smart-alerts"),
    path(
        "students/<int:student_id>/health-score/",
        views.StudentHealthScoreApi.as_view(),
        name="health-score",
    ),
    path(
        "students/<int:student_id>/predict/",
        views.PredictiveAnalyticsApi.as_view(),
        name="predictive",
    ),
    path(
        "students/<int:student_id>/report.pdf",
        views.StudentPdfReportApi.as_view(),
        name="student-report-pdf",
    ),
    path("admin/analytics/", views.AdminAnalyticsApi.as_view(), name="admin-analytics"),
    path("admin/chat-query/", views.AdminChatQueryApi.as_view(), name="admin-chat-query"),
]

