import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from models.upload import UploadResponse

router = APIRouter(tags=["Upload"])
client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]


def normalize_profile(profile: dict) -> dict:
    atsai     = profile.get("atsai_data", {})
    atsai_raw = atsai.get("raw", {})

    name  = profile.get("name") or atsai.get("name") or atsai_raw.get("name") or ""
    email = profile.get("email", "")
    if not email:
        email = name.lower().replace(" ", "") + "@effitrack.com" if name else "unknown@effitrack.com"

    reporting_to = profile.get("reportingTo", "")
    if isinstance(reporting_to, dict):
        reporting_to = reporting_to.get("name", "")

    social = atsai.get("social_links") or atsai_raw.get("social_links") or {}

    return {
        "uid":             profile.get("uid"),
        "name":            name,
        "email":           email,
        "phone":           profile.get("phone", ""),
        "gender":          profile.get("gender", ""),
        "address":         profile.get("address", ""),
        "college":         profile.get("college") or atsai.get("college") or atsai_raw.get("college", ""),
        "branch":          profile.get("branch") or atsai_raw.get("branch", ""),
        "year":            profile.get("year") or atsai_raw.get("year", ""),
        "education":       profile.get("education") or atsai.get("education", ""),
        "role":            profile.get("role", "Intern"),
        "position":        profile.get("position") or atsai.get("position") or atsai_raw.get("position", ""),
        "domain":          profile.get("domain") or atsai.get("domain", ""),
        "department":      profile.get("department", ""),
        "workMode":        profile.get("workMode", ""),
        "internshipType":  profile.get("internshipType", ""),
        "internshipDurationMonths": (
            profile.get("internshipDurationMonths") or
            profile.get("internshipDuration") or
            atsai_raw.get("internship_duration_months") or 0
        ),
        "joinDate":        profile.get("joinDate") or atsai_raw.get("joinDate", ""),
        "offerLetterRef":  profile.get("offerLetterRef") or atsai_raw.get("offer_letter_ref_no", ""),
        "reportingTo":     reporting_to,
        "status":          profile.get("status", "Active"),
        "ndaSigned":       profile.get("ndaSigned", False),
        "assessmentScore": (
            profile.get("assessmentScore") or
            atsai.get("assessment", {}).get("score") or
            atsai_raw.get("assessment", {}).get("score") or 0
        ),
        "assessmentFeedback": (
            profile.get("assessmentFeedback") or
            atsai.get("assessment", {}).get("feedback", "")
        ),
        "skills":          profile.get("skills") or atsai.get("skills") or atsai_raw.get("skills") or [],
        "certifications":  profile.get("certifications") or atsai_raw.get("certifications") or atsai.get("certifications") or [],
        "github":          profile.get("github") or social.get("github_url", ""),
        "linkedin":        profile.get("linkedin") or social.get("linkedin_url", ""),
        "summary":         profile.get("summary") or atsai.get("summary", ""),
        "profileImage":    profile.get("profileImage", ""),
        "priorProjects":   profile.get("priorProjects") or atsai.get("projects") or atsai_raw.get("projects") or [],
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_employee(file: UploadFile = File(...)):
    # file.filename is typed as str | None — a client can technically send
    # a file part with no filename, so guard before calling .endswith()
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files allowed")

    try:
        content = await file.read()
        raw     = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if "profile" not in raw:
        raise HTTPException(status_code=400, detail="JSON missing 'profile' key")

    profile = normalize_profile(raw["profile"])
    uid     = profile.get("uid")

    if not uid:
        raise HTTPException(status_code=400, detail="Profile missing uid")

    # upsert everything so re-uploading same file refreshes data
    await db["employees"].update_one(
        {"uid": uid}, {"$set": profile}, upsert=True
    )

    if "taskPerformance" in raw:
        data = raw["taskPerformance"]
        data["uid"] = uid
        await db["task_performance"].update_one(
            {"uid": uid}, {"$set": data}, upsert=True
        )

    if "attendance" in raw:
        data = raw["attendance"]
        data["uid"] = uid
        await db["raw_attendance"].update_one(
            {"uid": uid}, {"$set": data}, upsert=True
        )

    await db["projects"].update_one(
        {"uid": uid},
        {"$set": {"uid": uid, "priorProjects": profile.get("priorProjects", [])}},
        upsert=True
    )

    return {
        "success": True,
        "uid":     uid,
        "name":    profile.get("name", ""),
        "email":   profile.get("email", ""),
        "role":    profile.get("role", "Intern")
    }