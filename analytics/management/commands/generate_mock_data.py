from __future__ import annotations

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from analytics.models import Activity, Attendance, Grade, Student


FIRST_NAMES = [
    "Aarav",
    "Aditi",
    "Ananya",
    "Arjun",
    "Ishaan",
    "Kavya",
    "Neha",
    "Pranav",
    "Riya",
    "Sai",
    "Tanvi",
    "Varun",
    "Yash",
    "Zoya",
]
LAST_NAMES = [
    "Sharma",
    "Verma",
    "Patel",
    "Gupta",
    "Singh",
    "Khan",
    "Reddy",
    "Nair",
    "Iyer",
    "Jain",
]

SUBJECTS = {
    "CS": ["DSA", "DBMS", "OS", "CN", "AI"],
    "IT": ["Networks", "Web Tech", "DBMS", "Cloud", "Security"],
    "Mechanical": ["Thermo", "SOM", "FMHM", "CAD", "Manufacturing"],
}

ACADEMIC_ACTIVITIES = [
    "Peer tutoring",
    "Hackathon participation",
    "Research reading group",
    "Coding contest",
    "Lab assistantship",
]
EXTRA_ACTIVITIES = [
    "Sports club",
    "Music society",
    "Drama club",
    "Volunteer drive",
    "Photography walk",
]


def _full_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _cgpa_series(max_sem: int) -> list[float]:
    pattern = random.choices(
        ["improving", "declining", "mixed", "flat"], weights=[35, 20, 35, 10], k=1
    )[0]
    start = random.uniform(5.5, 9.0)
    series = []
    value = start
    for sem in range(1, max_sem + 1):
        if pattern == "improving":
            delta = random.uniform(0.05, 0.35)
        elif pattern == "declining":
            delta = -random.uniform(0.05, 0.35)
        elif pattern == "flat":
            delta = random.uniform(-0.08, 0.08)
        else:  # mixed
            delta = random.uniform(-0.25, 0.25)
        if sem >= max_sem - 1 and pattern == "declining" and random.random() < 0.35:
            delta -= random.uniform(0.2, 0.5)  # recent drops
        value = max(4.0, min(9.8, value + delta))
        series.append(round(value, 2))
    return series


class Command(BaseCommand):
    help = "Generate realistic mock dataset for CampusLedger"

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=200)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--wipe", action="store_true", help="Delete existing analytics data first")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        n_students = int(options["students"])
        wipe = bool(options["wipe"])

        if wipe:
            Attendance.objects.all().delete()
            Activity.objects.all().delete()
            Grade.objects.all().delete()
            Student.objects.all().delete()

        # divisions: A/B/C/D ~50 each for 200; spread for other totals
        divisions = (["A", "B", "C", "D"] * ((n_students // 4) + 1))[:n_students]
        random.shuffle(divisions)

        branches = ["CS", "IT", "Mechanical"]

        created = 0
        low_att_targets = set(random.sample(range(n_students), k=max(1, n_students // 6)))  # ~16%

        for i in range(n_students):
            branch = random.choice(branches)
            semester = random.randint(1, 8)
            student = Student.objects.create(
                name=_full_name(),
                branch=branch,
                semester=semester,
                division=divisions[i],
            )

            # grades 1..current semester (or at least 2 for trends)
            max_sem = max(2, semester)
            for sem, cgpa in enumerate(_cgpa_series(max_sem), start=1):
                Grade.objects.create(student=student, semester=sem, cgpa=cgpa)

            # attendance across last 90 days, 3 subjects
            subjects = random.sample(SUBJECTS[branch], k=3)
            start_date = date.today() - timedelta(days=90)
            for d in range(90):
                day = start_date + timedelta(days=d)
                if day.weekday() in (5, 6):  # weekend
                    continue
                for subject in subjects:
                    total = random.randint(1, 3)
                    # push some students below 75%
                    if i in low_att_targets:
                        attended = max(0, total - random.choice([1, 1, 2]))
                    else:
                        attended = total if random.random() < 0.75 else max(0, total - 1)
                    Attendance.objects.create(
                        student=student,
                        subject=subject,
                        total_classes=total,
                        attended_classes=attended,
                        date=day,
                    )

            # activities 5-10 per student over last 120 days
            n_act = random.randint(5, 10)
            for _ in range(n_act):
                is_academic = random.random() < 0.55
                act = random.choice(ACADEMIC_ACTIVITIES if is_academic else EXTRA_ACTIVITIES)
                day = date.today() - timedelta(days=random.randint(0, 120))
                Activity.objects.create(
                    student=student,
                    activity=act,
                    type="academic" if is_academic else "extracurricular",
                    date=day,
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} students with grades/attendance/activities."))

