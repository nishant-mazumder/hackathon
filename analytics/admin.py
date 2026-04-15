from django.contrib import admin

from .models import Activity, Attendance, Grade, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "branch", "semester", "division", "created_at")
    list_filter = ("branch", "semester", "division")
    search_fields = ("name",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "semester", "cgpa", "created_at")
    list_filter = ("semester",)
    search_fields = ("student__name",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "subject",
        "attended_classes",
        "total_classes",
        "date",
    )
    list_filter = ("subject", "date")
    search_fields = ("student__name", "subject")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "type", "activity", "date", "created_at")
    list_filter = ("type", "date")
    search_fields = ("student__name", "activity")
