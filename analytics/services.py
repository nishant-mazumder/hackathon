from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from django.db.models import Sum

from .models import Activity, Attendance, Grade, Student


def clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def calc_attendance_summary(student: Student) -> dict:
    agg = Attendance.objects.filter(student=student).aggregate(
        total=Sum("total_classes"), attended=Sum("attended_classes")
    )
    total = int(agg["total"] or 0)
    attended = int(agg["attended"] or 0)
    pct = (attended / total * 100.0) if total > 0 else 0.0
    return {"total_classes": total, "attended_classes": attended, "percent": pct}


def recovery_classes_needed(attended: int, total: int, target_pct: float = 75.0) -> int:
    """
    Minimum extra classes needed (and attended) to reach target_pct.
    (attended + x) / (total + x) >= target
    """
    if total <= 0:
        return 0
    target = target_pct / 100.0
    current = attended / total
    if current >= target:
        return 0
    # x >= (target*total - attended)/(1-target)
    x = (target * total - attended) / (1.0 - target)
    return int(math.ceil(x))


def grade_series(student: Student) -> list[dict]:
    grades = Grade.objects.filter(student=student).order_by("semester")
    return [{"semester": g.semester, "cgpa": float(g.cgpa)} for g in grades]


def cgpa_trend_slope(series: list[dict]) -> float:
    if len(series) < 2:
        return 0.0
    # simple slope: last - first over semesters span
    first = series[0]
    last = series[-1]
    denom = (last["semester"] - first["semester"]) or 1
    return (last["cgpa"] - first["cgpa"]) / denom


def recent_drop(series: list[dict], lookback: int = 2) -> float:
    if len(series) < lookback + 1:
        return 0.0
    last = series[-1]["cgpa"]
    prev = series[-(lookback + 1)]["cgpa"]
    return prev - last  # positive means drop


@dataclass(frozen=True)
class HealthScoreResult:
    score: int
    label: str
    reasons: list[str]
    recommendations: list[str]
    components: dict


def compute_health_score(student: Student) -> HealthScoreResult:
    attendance = calc_attendance_summary(student)
    att_pct = attendance["percent"]

    series = grade_series(student)
    slope = cgpa_trend_slope(series)
    drop = recent_drop(series, lookback=1)
    latest_cgpa = series[-1]["cgpa"] if series else 0.0

    since = date.today() - timedelta(days=60)
    activity_count_60 = Activity.objects.filter(student=student, date__gte=since).count()

    # Component scores
    cgpa_score = clamp((latest_cgpa / 10.0) * 40.0, 0.0, 40.0)
    trend_score = clamp((slope * 10.0) * 10.0 + 10.0, 0.0, 20.0)  # centered
    attendance_score = clamp((att_pct / 100.0) * 30.0, 0.0, 30.0)
    activity_score = clamp((activity_count_60 / 12.0) * 10.0, 0.0, 10.0)

    penalty = 0.0
    if drop >= 0.5:
        penalty += 6.0
    if att_pct < 75.0:
        penalty += 10.0
    if activity_count_60 == 0:
        penalty += 2.0

    raw = cgpa_score + trend_score + attendance_score + activity_score - penalty
    score = int(round(clamp(raw, 0.0, 100.0)))

    reasons: list[str] = []
    recs: list[str] = []
    if att_pct < 75.0:
        reasons.append(f"Attendance is low ({att_pct:.1f}%).")
        needed = recovery_classes_needed(
            attendance["attended_classes"], attendance["total_classes"], 75.0
        )
        recs.append(f"Attend the next {needed} classes consistently to recover to 75%.")
    if latest_cgpa < 6.5:
        reasons.append(f"Latest CGPA is below target ({latest_cgpa:.2f}).")
        recs.append("Prioritize weak subjects and follow a weekly revision plan.")
    if slope < -0.05:
        reasons.append("CGPA trend is declining.")
        recs.append("Book mentoring sessions and focus on fundamentals to stop the decline.")
    if activity_count_60 < 3:
        reasons.append("Low activity participation recently.")
        recs.append("Add 1–2 academic/extracurricular activities per month to improve engagement.")

    if score >= 80:
        label = "Excellent"
        if not reasons:
            reasons = ["Consistent performance across grades, attendance, and engagement."]
        if not recs:
            recs = ["Keep current habits; aim for incremental CGPA improvements next semester."]
    elif score >= 55:
        label = "At Risk"
        if not reasons:
            reasons = ["Some metrics indicate risk; targeted improvements can quickly help."]
        if not recs:
            recs = ["Improve attendance consistency and stabilize CGPA trend."]
    else:
        label = "Critical"
        if not reasons:
            reasons = ["Multiple indicators show urgent academic risk."]
        if not recs:
            recs = ["Immediate intervention: attendance recovery + tutoring + weekly progress reviews."]

    return HealthScoreResult(
        score=score,
        label=label,
        reasons=reasons,
        recommendations=recs,
        components={
            "latest_cgpa": latest_cgpa,
            "cgpa_trend_slope": slope,
            "attendance_percent": att_pct,
            "activity_count_60d": activity_count_60,
            "penalty": penalty,
        },
    )


def predict_next_cgpa(student: Student) -> dict:
    series = grade_series(student)
    if not series:
        return {"predicted_cgpa": 0.0, "risk_level": "High", "method": "insufficient_data"}
    if len(series) == 1:
        pred = float(series[-1]["cgpa"])
    else:
        # average delta over last 3 transitions
        last = series[-4:] if len(series) >= 4 else series
        deltas = []
        for i in range(1, len(last)):
            deltas.append(last[i]["cgpa"] - last[i - 1]["cgpa"])
        pred = float(series[-1]["cgpa"] + mean(deltas))
    pred = float(clamp(pred, 0.0, 10.0))

    attendance = calc_attendance_summary(student)["percent"]
    health = compute_health_score(student).score
    if health >= 75 and attendance >= 80:
        risk = "Low"
    elif health >= 55 and attendance >= 70:
        risk = "Medium"
    else:
        risk = "High"

    return {"predicted_cgpa": pred, "risk_level": risk, "method": "trend_extrapolation"}

