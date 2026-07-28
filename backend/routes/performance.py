from fastapi import APIRouter, HTTPException
from database import employee_collection
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from models.performance import PerformanceOut

router = APIRouter(prefix="/employees", tags=["Performance"])
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


def calculate_on_time_percentage(on_time, delayed):
    total = on_time + delayed
    return round((on_time / total) * 100, 2) if total else 0

def calculate_overall_score(tp):
    done    = tp.get("doneTasks", 0)
    pending = tp.get("pendingTasks", 0)
    total   = done + pending
    completion_rate = (done / max(total, 1)) * 100
    on_time_rate    = calculate_on_time_percentage(
        tp.get("onTimeCompletions", 0), tp.get("lateCompletions", 0)
    )
    subtask_rate = (tp.get("subtasksDone", 0) / max(tp.get("subtasksTotal", 1), 1)) * 100
    return round(completion_rate * 0.4 + on_time_rate * 0.4 + subtask_rate * 0.2, 2)

def get_weekly_consistency(tp):
    return [
        {"week": w.get("week", "Unknown"), "completed_tasks": w.get("done", 0)}
        for w in tp.get("byPhase", [])
    ]


async def compute_employee_average_score():
    """One bulk query across every employee's task_performance record —
    not a per-employee loop — so this stays cheap regardless of headcount."""
    all_tp = await db["task_performance"].find({}, {"_id": 0}).to_list(length=None)
    if not all_tp:
        return 0.0
    scores = [calculate_overall_score(tp) for tp in all_tp]
    return round(sum(scores) / len(scores), 2)


@router.get("/{uid}/performance", response_model=PerformanceOut)
async def get_performance(uid: str):
    employee = await employee_collection.find_one({"uid": uid})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    tp = await db["task_performance"].find_one({"uid": uid}, {"_id": 0})
    if not tp:
        raise HTTPException(status_code=404, detail="Performance data not found")

    on_time        = tp.get("onTimeCompletions", 0)
    delayed        = tp.get("lateCompletions", 0)
    on_time_pct    = calculate_on_time_percentage(on_time, delayed)
    overall_score  = calculate_overall_score(tp)
    employee_avg   = await compute_employee_average_score()

    return {
        "tasks_completed_before_deadline": on_time,
        "delayed_tasks":                   delayed,
        "on_time_delivery_percentage":     on_time_pct,
        "weekly_consistency":              get_weekly_consistency(tp),
        "overall_performance_score":       overall_score,
        "employee_average_score":          employee_avg,
        "performance_metrics": {
            "on_time_tasks":               on_time,
            "delayed_tasks":               delayed,
            "on_time_delivery_percentage": on_time_pct,
            "overall_performance_score":   overall_score
        }
    }