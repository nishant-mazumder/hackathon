from rest_framework import serializers

from .models import Activity, Attendance, Grade, Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "branch", "semester", "division", "created_at"]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "student", "semester", "cgpa", "created_at"]


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "subject",
            "total_classes",
            "attended_classes",
            "date",
            "created_at",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ["id", "student", "activity", "type", "date", "created_at"]

