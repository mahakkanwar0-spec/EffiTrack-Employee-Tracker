from fastapi import APIRouter, HTTPException
from database import employee_collection
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from models.attendance import AttendanceOut
# from datetime import datetime
# from zoneinfo import ZoneInfo

# def format_time(timestamp):
#     if not timestamp:
#         return "N/A"

#     dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
#     dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))
#     return dt.strftime("%I:%M %p")

router = APIRouter(prefix="/employees", tags=["Attendance"])

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


async def compute_company_average():
    """One bulk query across every attendance record — not a per-employee
    loop — so this stays cheap regardless of how many employees exist."""
    all_att = await db["raw_attendance"].find({}, {"_id": 0}).to_list(length=None)
    if not all_att:
        return {"avg_attendance_percentage": 0, "avg_late_arrivals": 0, "avg_hours": 0}

    pct_values   = []
    late_values  = []
    hours_values = []

    for a in all_att:
        present    = a.get("presentDays", 0)
        total_days = a.get("totalDays", 0)
        pct_values.append(round((present / total_days) * 100, 2) if total_days else 0)
        late_values.append(a.get("lateArrivals", 0))
        hours_values.append(a.get("avgHours", 0))

    count = len(all_att)
    return {
        "avg_attendance_percentage": round(sum(pct_values) / count, 2),
        "avg_late_arrivals":         round(sum(late_values) / count, 2),
        "avg_hours":                 round(sum(hours_values) / count, 2),
    }


@router.get("/{uid}/attendance", response_model=AttendanceOut)
async def get_attendance(uid: str):
    employee = await employee_collection.find_one({"uid": uid})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    attendance = await db["raw_attendance"].find_one({"uid": uid}, {"_id": 0})
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance data not found")
    
    notification = await db["notifications"].find_one({"uid": uid}, {"_id": 0})
    if not notification:
      notification = {}

    present = attendance.get("presentDays", 0)
    total_days = attendance.get("totalDays", 0)
    att_pct = round((present / total_days) * 100, 2) if total_days else 0

    company_average = await compute_company_average()

    return {
        "attendance_percentage": att_pct,
        "present_days": present,
        "leave_days": attendance.get("leaveDays", 0),
        "late_arrivals": attendance.get("lateArrivals", 0),
        "working_hours": {
            "average_hours": attendance.get("avgHours", 0),
            "total_hours": attendance.get("totalHours", 0),
        },
        "checkin_checkout": {
            "earliest_checkin":notification.get("earliestAt", "N/A"),
            "latest_checkout": notification.get("latestAt", "N/A"),
        },
        "short_days": attendance.get("shortDays", 0),
        "missed_checkouts": attendance.get("missedCheckouts", 0),
        "idle_warning_days": attendance.get("idleWarningDays", 0),
        "geo_out_of_range_days": attendance.get("geoOutOfRangeDays", 0),
        "company_average": company_average,
    }