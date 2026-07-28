from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

router = APIRouter(tags=["Achievements"])
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


def calculate_score(tp, attendance, profile):
    total      = tp.get("totalTasks", 1)
    done       = tp.get("doneTasks", 0)
    ontime     = tp.get("onTimeCompletions", 0)
    present    = attendance.get("presentDays", 0)
    total_days = attendance.get("totalDays", 1)
    assessment = profile.get("assessmentScore", 0)

    completion_rate  = round((done / total) * 100, 2) if total else 0
    ontime_rate      = round((ontime / done) * 100, 2) if done else 0
    attendance_rate  = round((present / total_days) * 100, 2) if total_days else 0
    score = round(
        completion_rate * 0.40 + ontime_rate * 0.30 +
        attendance_rate * 0.20 + assessment * 0.10, 2
    )
    return {
        "score": score, "completion_rate": completion_rate,
        "ontime_rate": ontime_rate, "attendance_rate": attendance_rate,
        "assessment_score": assessment
    }


def derive_achievements(tp, attendance):
    achievements = []
    if attendance.get("presentDays") == attendance.get("totalDays"):
        achievements.append({"title": "Perfect Attendance",
                             "description": f"Present all {attendance['totalDays']} working days"})
    if tp.get("lateCompletions") == 0 and tp.get("doneTasks", 0) > 0:
        achievements.append({"title": "On-Time Champion",
                             "description": "Completed every task on or before deadline"})
    for phase in tp.get("byPhase", []):
        if phase.get("total") == phase.get("done") and phase.get("done", 0) > 0:
            achievements.append({"title": "Phase Complete",
                                 "description": f"Finished all tasks in: {phase['week']}"})
    total, done = tp.get("totalTasks", 1), tp.get("doneTasks", 0)
    if done / total >= 0.5:
        achievements.append({"title": "Halfway Hero",
                             "description": f"Completed {done} out of {total} tasks"})
    sub_done, sub_total = tp.get("subtasksDone", 0), tp.get("subtasksTotal", 1)
    if sub_done / sub_total >= 0.5:
        achievements.append({"title": "Subtask Finisher",
                             "description": f"Completed {sub_done} of {sub_total} subtasks"})
    return achievements


# ── shared bulk fetch: 3 queries total instead of 1 + 2*N ──────
async def compute_all_scores():
    """Fetch every employee's score in bulk (3 DB round-trips total,
    regardless of company size) instead of looping and querying per employee."""
    employees = await db["employees"].find({}, {"_id": 0}).to_list(length=None)
    uids = [e["uid"] for e in employees if e.get("uid")]

    tp_docs  = await db["task_performance"].find(
        {"uid": {"$in": uids}}, {"_id": 0}
    ).to_list(length=None)
    att_docs = await db["raw_attendance"].find(
        {"uid": {"$in": uids}}, {"_id": 0}
    ).to_list(length=None)

    tp_map  = {d["uid"]: d for d in tp_docs}
    att_map = {d["uid"]: d for d in att_docs}

    results = []
    for emp in employees:
        uid = emp.get("uid")
        tp  = tp_map.get(uid)
        att = att_map.get(uid)
        if tp and att:
            metrics = calculate_score(tp, att, emp)
            results.append({
                "uid": uid,
                "name": tp.get("internName", emp.get("email", "Unknown")),
                **metrics
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, entry in enumerate(results):
        entry["rank"] = i + 1
    return results


@router.get("/employees/{uid}/achievements")
async def get_achievements(uid: str):
    profile    = await db["employees"].find_one({"uid": uid}, {"_id": 0})
    tp         = await db["task_performance"].find_one({"uid": uid}, {"_id": 0})
    attendance = await db["raw_attendance"].find_one({"uid": uid}, {"_id": 0})

    if not profile:    raise HTTPException(status_code=404, detail="Employee not found")
    if not tp:         raise HTTPException(status_code=404, detail="Task performance not found")
    if not attendance: raise HTTPException(status_code=404, detail="Attendance not found")

    metrics      = calculate_score(tp, attendance, profile)
    achievements = derive_achievements(tp, attendance)

    all_scores = await compute_all_scores()
    rank = next((s["rank"] for s in all_scores if s["uid"] == uid), None)

    return {"uid": uid, **metrics, "achievements": achievements, "rank_in_company": rank}


@router.get("/leaderboard")
async def get_leaderboard():
    return await compute_all_scores()