from __future__ import annotations

import re
from datetime import date, timedelta

from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Activity, Attendance, Grade, Student
from .serializers import ActivitySerializer, StudentSerializer
from .services import calc_attendance_summary, compute_health_score, predict_next_cgpa, recovery_classes_needed


class StudentListApi(APIView):
    def get(self, request):
        qs = Student.objects.all().order_by("id")
        branch = request.query_params.get("branch")
        semester = request.query_params.get("semester")
        division = request.query_params.get("division")
        if branch:
            qs = qs.filter(branch=branch)
        if semester:
            qs = qs.filter(semester=int(semester))
        if division:
            qs = qs.filter(division=division)
        return Response(StudentSerializer(qs, many=True).data)


class StudentProfileApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        grades = Grade.objects.filter(student=student).order_by("semester")
        attendance = calc_attendance_summary(student)
        health = compute_health_score(student)
        return Response(
            {
                "student": StudentSerializer(student).data,
                "latest_grade": {
                    "semester": grades.last().semester if grades.exists() else None,
                    "cgpa": float(grades.last().cgpa) if grades.exists() else None,
                },
                "attendance": attendance,
                "health": {
                    "score": health.score,
                    "label": health.label,
                    "reasons": health.reasons,
                    "recommendations": health.recommendations,
                    "components": health.components,
                },
            }
        )


class GradeTrendApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        series = Grade.objects.filter(student=student).order_by("semester")
        return Response(
            {
                "student_id": student.id,
                "trend": [{"semester": g.semester, "cgpa": float(g.cgpa)} for g in series],
            }
        )


class AttendanceHeatmapApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        days = int(request.query_params.get("days", "90"))
        since = date.today() - timedelta(days=days)
        qs = (
            Attendance.objects.filter(student=student, date__gte=since)
            .values("date")
            .annotate(total=Sum("total_classes"), attended=Sum("attended_classes"))
            .order_by("date")
        )
        data = []
        for row in qs:
            total = int(row["total"] or 0)
            attended = int(row["attended"] or 0)
            pct = (attended / total * 100.0) if total else 0.0
            data.append({"date": row["date"].isoformat(), "percent": pct})
        return Response({"student_id": student.id, "days": days, "heatmap": data})


class ActivityTimelineApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        limit = int(request.query_params.get("limit", "50"))
        qs = Activity.objects.filter(student=student).order_by("-date", "-id")[:limit]
        return Response({"student_id": student.id, "timeline": ActivitySerializer(qs, many=True).data})


class SmartAlertApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        att = calc_attendance_summary(student)
        alerts = []
        if att["total_classes"] > 0 and att["percent"] < 75.0:
            needed = recovery_classes_needed(att["attended_classes"], att["total_classes"], 75.0)
            alerts.append(
                {
                    "type": "attendance",
                    "severity": "high" if att["percent"] < 60 else "medium",
                    "message": f"Attendance is {att['percent']:.1f}% (<75%).",
                    "recovery_classes_needed": needed,
                }
            )
        return Response({"student_id": student.id, "alerts": alerts})


class StudentHealthScoreApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        res = compute_health_score(student)
        return Response(
            {
                "student_id": student.id,
                "score": res.score,
                "label": res.label,
                "reasons": res.reasons,
                "recommendations": res.recommendations,
                "components": res.components,
            }
        )


class PredictiveAnalyticsApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        pred = predict_next_cgpa(student)
        return Response({"student_id": student.id, **pred})


class AdminAnalyticsApi(APIView):
    def get(self, request):
        branch = request.query_params.get("branch")
        semester = request.query_params.get("semester")
        subject = request.query_params.get("subject")

        students = Student.objects.all()
        if branch:
            students = students.filter(branch=branch)
        if semester:
            students = students.filter(semester=int(semester))

        # Latest CGPA per student (approx: average of their highest semester record)
        latest_grade = (
            Grade.objects.filter(student__in=students)
            .values("student_id")
            .annotate(latest_sem=Sum("semester"))
        )
        # Simpler: pick top by max cgpa across records
        top = (
            Grade.objects.filter(student__in=students)
            .values("student_id", "student__name", "student__branch", "student__semester", "student__division")
            .annotate(best_cgpa=Avg("cgpa"))
            .order_by("-best_cgpa")[:10]
        )

        # At-risk: attendance below 75 OR health score below 55 (computed per student, capped)
        at_risk = []
        for s in students[:500]:
            att = calc_attendance_summary(s)["percent"]
            hs = compute_health_score(s).score
            if att < 75.0 or hs < 55:
                at_risk.append(
                    {
                        "id": s.id,
                        "name": s.name,
                        "branch": s.branch,
                        "semester": s.semester,
                        "division": s.division,
                        "attendance_percent": att,
                        "health_score": hs,
                    }
                )
        at_risk = sorted(at_risk, key=lambda r: (r["health_score"], r["attendance_percent"]))[:25]

        dept_stats = (
            Grade.objects.values("student__branch")
            .annotate(avg_cgpa=Avg("cgpa"), n=Count("id"))
            .order_by("student__branch")
        )

        attendance_qs = Attendance.objects.all()
        if subject:
            attendance_qs = attendance_qs.filter(subject__icontains=subject)
        if branch:
            attendance_qs = attendance_qs.filter(student__branch=branch)
        if semester:
            attendance_qs = attendance_qs.filter(student__semester=int(semester))

        subject_difficulty = (
            attendance_qs.values("subject")
            .annotate(total=Sum("total_classes"), attended=Sum("attended_classes"))
            .order_by("subject")
        )
        subj_out = []
        for row in subject_difficulty:
            total = int(row["total"] or 0)
            attended = int(row["attended"] or 0)
            pct = (attended / total * 100.0) if total else 0.0
            subj_out.append({"subject": row["subject"], "attendance_percent": pct})
        subj_out = sorted(subj_out, key=lambda r: r["attendance_percent"])[:10]

        return Response(
            {
                "top_students": list(top),
                "at_risk_students": at_risk,
                "department_stats": list(dept_stats),
                "subject_difficulty": subj_out,
            }
        )


def _parse_admin_query(text: str) -> dict:
    t = (text or "").lower()
    out: dict = {}

    m = re.search(r"attendance\s+below\s+(\d{1,3})\s*%?", t)
    if m:
        out["attendance_below"] = int(m.group(1))

    m = re.search(r"\bsem(?:ester)?\s*(\d)\b", t)
    if m:
        out["semester"] = int(m.group(1))

    m = re.search(r"\b(branch|dept)\s*(cs|it|mechanical)\b", t)
    if m:
        out["branch"] = m.group(2).upper() if m.group(2) in ("cs", "it") else "Mechanical"

    m = re.search(r"\bdivision\s*([abcd])\b", t)
    if m:
        out["division"] = m.group(1).upper()

    return out


class AdminChatQueryApi(APIView):
    def post(self, request):
        query = request.data.get("query", "")
        parsed = _parse_admin_query(query)

        qs = Student.objects.all()
        if "branch" in parsed:
            qs = qs.filter(branch=parsed["branch"])
        if "semester" in parsed:
            qs = qs.filter(semester=parsed["semester"])
        if "division" in parsed:
            qs = qs.filter(division=parsed["division"])

        threshold = parsed.get("attendance_below")
        results = []
        for s in qs[:800]:
            att = calc_attendance_summary(s)["percent"]
            if threshold is None or att < threshold:
                results.append(
                    {
                        "id": s.id,
                        "name": s.name,
                        "branch": s.branch,
                        "semester": s.semester,
                        "division": s.division,
                        "attendance_percent": att,
                    }
                )
        results = sorted(results, key=lambda r: r["attendance_percent"])
        return Response({"query": query, "parsed": parsed, "count": len(results), "results": results[:50]})


class StudentPdfReportApi(APIView):
    def get(self, request, student_id: int):
        student = get_object_or_404(Student, id=student_id)
        grades = Grade.objects.filter(student=student).order_by("semester")
        att = calc_attendance_summary(student)
        health = compute_health_score(student)
        pred = predict_next_cgpa(student)

        resp = HttpResponse(content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="CampusLedger_Student_{student.id}.pdf"'

        c = canvas.Canvas(resp, pagesize=letter)
        width, height = letter
        y = height - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "CampusLedger - Student Report")
        y -= 30

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Student: {student.name} (ID: {student.id})")
        y -= 16
        c.drawString(50, y, f"Branch: {student.branch} | Semester: {student.semester} | Division: {student.division}")
        y -= 24

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Grades (CGPA trend)")
        y -= 16
        c.setFont("Helvetica", 11)
        for g in grades:
            c.drawString(60, y, f"Sem {g.semester}: {float(g.cgpa):.2f}")
            y -= 14
            if y < 120:
                c.showPage()
                y = height - 50

        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Attendance Summary")
        y -= 16
        c.setFont("Helvetica", 11)
        c.drawString(
            60,
            y,
            f"Attended: {att['attended_classes']} / {att['total_classes']} ({att['percent']:.1f}%)",
        )
        y -= 22

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Health Score")
        y -= 16
        c.setFont("Helvetica", 11)
        c.drawString(60, y, f"Score: {health.score} / 100  |  Label: {health.label}")
        y -= 16
        c.drawString(60, y, "Key reasons:")
        y -= 14
        for r in health.reasons[:6]:
            c.drawString(75, y, f"- {r}")
            y -= 14
        y -= 8
        c.drawString(60, y, "Recommendations:")
        y -= 14
        for r in health.recommendations[:6]:
            c.drawString(75, y, f"- {r}")
            y -= 14

        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Prediction")
        y -= 16
        c.setFont("Helvetica", 11)
        c.drawString(60, y, f"Next semester predicted CGPA: {pred['predicted_cgpa']:.2f}")
        y -= 14
        c.drawString(60, y, f"Risk level: {pred['risk_level']}")

        c.showPage()
        c.save()
        return resp
