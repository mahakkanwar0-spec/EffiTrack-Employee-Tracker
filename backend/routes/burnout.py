from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from models.burnout import BurnoutOut
import pickle, numpy as np

router = APIRouter(tags=["Burnout"])
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

with open("ml/burnout/burnout_model.pkl", "rb") as f:
    saved   = pickle.load(f)
    model   = saved["model"]
    encoder = saved["encoder"]

RISK_EMOJI = {
    "Low":    "🟢 Low Risk",
    "Medium": "🟡 Medium Risk",
    "High":   "🔴 High Risk"
}

FEATURE_ORDER = [
    "avgHours", "totalHours", "attendance",
    "lateArrivals", "missedCheckouts", "idleWarningDays",
    "geoOutOfRange", "pendingTasks", "overdueTasks"
]


def build_features(attendance: dict, tp: dict) -> list:
    present    = attendance.get("presentDays", 0)
    total_days = attendance.get("totalDays", 1)
    attendance_pct = round((present / total_days) * 100, 2) if total_days else 0

    return [
        attendance.get("avgHours", 0),
        attendance.get("totalHours", 0),
        attendance_pct,
        attendance.get("lateArrivals", 0),
        attendance.get("missedCheckouts", 0),
        attendance.get("idleWarningDays", 0),
        attendance.get("geoOutOfRangeDays", 0),
        tp.get("pendingTasks", 0),
        tp.get("overdueTasks", 0),
    ]


async def compute_company_burnout_comparison(target_uid: str, your_risk_score: float):
    """One bulk fetch + one batch model.predict() call across every employee
    who has both attendance and task-performance data — not a per-employee
    loop of individual .predict() calls."""
    employees = await db["employees"].find({}, {"_id": 0}).to_list(length=None)
    uids = [e["uid"] for e in employees if e.get("uid")]

    att_docs = await db["raw_attendance"].find(
        {"uid": {"$in": uids}}, {"_id": 0}
    ).to_list(length=None)
    tp_docs  = await db["task_performance"].find(
        {"uid": {"$in": uids}}, {"_id": 0}
    ).to_list(length=None)

    att_map = {d["uid"]: d for d in att_docs}
    tp_map  = {d["uid"]: d for d in tp_docs}

    feature_rows = []
    for emp in employees:
        uid = emp.get("uid")
        att = att_map.get(uid)
        tp  = tp_map.get(uid)
        if att and tp:
            feature_rows.append(build_features(att, tp))

    if not feature_rows:
        return {
            "risk_distribution": {"Low": 0.0, "Medium": 0.0, "High": 0.0},
            "avg_risk_score": 0.0,
            "your_risk_score": your_risk_score,
            "total_employees": 0
        }

    X = np.array(feature_rows)
    preds  = model.predict(X)
    probs  = model.predict_proba(X)
    labels = encoder.inverse_transform(preds)

    low_idx = list(encoder.classes_).index("Low") if "Low" in encoder.classes_ else None

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    risk_scores = []
    for i, lbl in enumerate(labels):
        risk_counts[lbl] = risk_counts.get(lbl, 0) + 1
        if low_idx is not None:
            risk_scores.append(round(100 - probs[i][low_idx] * 100, 2))

    total = len(feature_rows)
    risk_distribution = {k: round((v / total) * 100, 2) for k, v in risk_counts.items()}
    avg_risk_score = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0

    return {
        "risk_distribution": risk_distribution,
        "avg_risk_score": avg_risk_score,
        "your_risk_score": your_risk_score,
        "total_employees": total
    }


@router.get("/employees/{uid}/burnout", response_model=BurnoutOut)
async def predict_burnout(uid: str):
    employee   = await db["employees"].find_one({"uid": uid}, {"_id": 0})
    attendance = await db["raw_attendance"].find_one({"uid": uid}, {"_id": 0})
    tp         = await db["task_performance"].find_one({"uid": uid}, {"_id": 0})

    if not employee:   raise HTTPException(status_code=404, detail="Employee not found")
    if not attendance: raise HTTPException(status_code=404, detail="Attendance not found")
    if not tp:         raise HTTPException(status_code=404, detail="Task performance not found")

    feature_values = build_features(attendance, tp)
    features = np.array([feature_values])

    pred_encoded  = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    risk_label    = encoder.inverse_transform([pred_encoded])[0]
    prob_dict     = {encoder.classes_[i]: round(float(probabilities[i]) * 100, 2)
                     for i in range(len(encoder.classes_))}

    low_val = prob_dict.get("Low", 0)
    your_risk_score = round(100 - low_val, 2)

    company_comparison = await compute_company_burnout_comparison(uid, your_risk_score)

    return {
        "uid":        uid,
        "risk_level": risk_label,
        "risk_label": RISK_EMOJI[risk_label],
        "probabilities": prob_dict,
        "input_features": dict(zip(FEATURE_ORDER, feature_values)),
        "company_comparison": company_comparison
    }