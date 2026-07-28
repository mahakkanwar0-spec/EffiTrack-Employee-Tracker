from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from models.performance_score import PerformanceScoreOut
import pickle, numpy as np

router = APIRouter(tags=["Performance Score"])
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

with open("ml/score/score_model.pkl", "rb") as f:
    saved      = pickle.load(f)
    score_model = saved["model"]
    model_name  = saved["model_name"]


def get_grade(score):
    if score >= 90: return "A+", "#2ecc71"
    elif score >= 80: return "A", "#27ae60"
    elif score >= 70: return "B", "#f39c12"
    elif score >= 60: return "C", "#e67e22"
    else: return "D", "#e74c3c"

def get_contribution(features):
    tips = {}
    tips["Attendance"]      = "🟢 Excellent" if features["attendance"] >= 95 else ("🟡 Good" if features["attendance"] >= 80 else "🔴 Needs Improvement")
    tips["Task Completion"] = "🟢 Excellent" if features["completion"] >= 90 else ("🟡 Good" if features["completion"] >= 70 else "🔴 Needs Improvement")
    tips["Punctuality"]     = "🟢 Excellent" if features["late_arrivals"] <= 2 else ("🟡 Moderate" if features["late_arrivals"] <= 6 else "🔴 High Late Arrivals")
    tips["Working Hours"]   = "🟢 On Track"  if features["hours"] >= 8 else ("🟡 Below Average" if features["hours"] >= 6 else "🔴 Low Hours")
    tips["Projects"]        = "🟢 High Involvement" if features["projects"] >= 5 else ("🟡 Moderate" if features["projects"] >= 3 else "🔴 Low Involvement")
    return tips


@router.get("/employees/{uid}/performance-score", response_model=PerformanceScoreOut)
async def predict_performance_score(
    uid: str,
):
    employee   = await db["employees"].find_one({"uid": uid}, {"_id": 0})
    attendance = await db["raw_attendance"].find_one({"uid": uid}, {"_id": 0})
    tp         = await db["task_performance"].find_one({"uid": uid}, {"_id": 0})

    if not employee:   raise HTTPException(status_code=404, detail="Employee not found")
    if not attendance: raise HTTPException(status_code=404, detail="Attendance not found")
    if not tp:         raise HTTPException(status_code=404, detail="Task performance not found")

    present        = attendance.get("presentDays", 0)
    total_days     = attendance.get("totalDays", 1)
    attendance_pct = round((present / total_days) * 100, 2)
    done           = tp.get("doneTasks", 0)
    total          = tp.get("totalTasks", 1)
    completion_rate= round((done / total) * 100, 2)
    tasks          = tp.get("tasks", [])
    projects       = len(set(t.get("project") for t in tasks if t.get("project")))
    avg_hours      = attendance.get("avgHours", 0)
    late_arrivals  = attendance.get("lateArrivals", 0)

    features = {
        "attendance":   attendance_pct,
        "completion":   completion_rate,
        "projects":     projects,
        "hours":        avg_hours,
        "late_arrivals":late_arrivals
    }

    X = np.array([[attendance_pct, completion_rate, projects, avg_hours, late_arrivals]])
    predicted  = round(float(np.clip(score_model.predict(X)[0], 0, 100)), 2)
    grade, gc  = get_grade(predicted)

    return {
        "uid": uid, "predicted_score": predicted,
        "grade": grade, "grade_color": gc,
        "model_used": model_name,
        "input_features": features,
        "feature_contribution": get_contribution(features)
    }