from django.db import models


class Student(models.Model):
    BRANCH_CHOICES = [
        ("CS", "CS"),
        ("IT", "IT"),
        ("Mechanical", "Mechanical"),
    ]
    DIVISION_CHOICES = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]

    name = models.CharField(max_length=120)
    branch = models.CharField(max_length=20, choices=BRANCH_CHOICES)
    semester = models.PositiveSmallIntegerField()
    division = models.CharField(max_length=1, choices=DIVISION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["branch", "semester"]),
            models.Index(fields=["division"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.branch} Sem {self.semester}{self.division})"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grades")
    semester = models.PositiveSmallIntegerField()
    cgpa = models.DecimalField(max_digits=3, decimal_places=2)  # 0.00 - 10.00
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("student", "semester")]
        indexes = [
            models.Index(fields=["student", "semester"]),
            models.Index(fields=["semester", "cgpa"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} Sem {self.semester} CGPA {self.cgpa}"


class Attendance(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    subject = models.CharField(max_length=100)
    total_classes = models.PositiveSmallIntegerField()
    attended_classes = models.PositiveSmallIntegerField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "date"]),
            models.Index(fields=["subject", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} {self.subject} {self.date}"


class Activity(models.Model):
    TYPE_CHOICES = [
        ("academic", "academic"),
        ("extracurricular", "extracurricular"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="activities")
    activity = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "date"]),
            models.Index(fields=["type", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} {self.type} {self.activity}"
