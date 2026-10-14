import json
import asyncio
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

import os

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "effitrack")
DATA_FOLDER = "data"


def normalize_profile(profile: dict) -> dict:
    """Handles both old flat format and new atsai_data nested format."""

    atsai      = profile.get("atsai_data", {})
    atsai_raw  = atsai.get("raw", {})

    # ── name ──────────────────────────────────────────────────
    name = (
        profile.get("name") or
        atsai.get("name") or
        atsai_raw.get("name") or
        ""
    )

    # ── email ─────────────────────────────────────────────────
    email = profile.get("email", "")
    if not email:
        # generate from name if missing (new format has no email)
        if name:
            email = name.lower().replace(" ", "") + "@effitrack.com"
        else:
            email = profile.get("uid", "unknown")[:8] + "@effitrack.com"

    # ── reportingTo ───────────────────────────────────────────
    reporting_to = profile.get("reportingTo", "")
    if isinstance(reporting_to, dict):
        reporting_to = reporting_to.get("name", "")

    # ── assessmentScore ───────────────────────────────────────
    assessment_score = (
        profile.get("assessmentScore") or
        atsai.get("assessment", {}).get("score") or
        atsai_raw.get("assessment", {}).get("score") or
        0
    )

    # ── skills ────────────────────────────────────────────────
    skills = (
        profile.get("skills") or
        atsai.get("skills") or
        atsai_raw.get("skills") or
        []
    )

    # ── certifications ────────────────────────────────────────
    certifications = (
        profile.get("certifications") or
        atsai_raw.get("certifications") or
        atsai.get("certifications") or
        []
    )

    # ── college ───────────────────────────────────────────────
    college = (
        profile.get("college") or
        atsai.get("college") or
        atsai_raw.get("college") or
        ""
    )

    # ── education ─────────────────────────────────────────────
    education = (
        profile.get("education") or
        atsai.get("education") or
        atsai_raw.get("education") or
        ""
    )

    # ── position ──────────────────────────────────────────────
    position = (
        profile.get("position") or
        atsai.get("position") or
        atsai_raw.get("position") or
        ""
    )

    # ── domain ────────────────────────────────────────────────
    domain = (
        profile.get("domain") or
        atsai.get("domain") or
        atsai_raw.get("domain") or
        ""
    )

    # ── github / linkedin ─────────────────────────────────────
    social      = atsai.get("social_links") or atsai_raw.get("social_links") or {}
    github      = profile.get("github") or social.get("github_url", "")
    linkedin    = profile.get("linkedin") or social.get("linkedin_url", "")

    # ── summary ───────────────────────────────────────────────
    summary = (
        profile.get("summary") or
        atsai.get("summary") or
        ""
    )

    # ── priorProjects ─────────────────────────────────────────
    prior_projects = (
        profile.get("priorProjects") or
        atsai.get("projects") or
        atsai_raw.get("projects") or
        []
    )

    # ── other flat fields ─────────────────────────────────────
    return {
        "uid":                  profile.get("uid"),
        "name":                 name,
        "email":                email,
        "phone":                profile.get("phone", ""),
        "dob":                  profile.get("dob", ""),
        "gender":               profile.get("gender", ""),
        "address":              profile.get("address", ""),
        "college":              college,
        "branch":               profile.get("branch") or atsai_raw.get("branch", ""),
        "year":                 profile.get("year") or atsai_raw.get("year", ""),
        "graduation_year":      profile.get("graduation_year") or atsai_raw.get("graduation_year"),
        "roll_no":              profile.get("roll_no") or atsai_raw.get("roll_no", ""),
        "education":            education,
        "role":                 profile.get("role", "Intern"),
        "position":             position,
        "domain":               domain,
        "department":           profile.get("department", ""),
        "workMode":             profile.get("workMode", ""),
        "internshipType":       profile.get("internshipType", ""),
        "internshipDurationMonths": (
            profile.get("internshipDurationMonths") or
            profile.get("internshipDuration") or
            atsai_raw.get("internship_duration_months") or 0
        ),
        "joinDate":             profile.get("joinDate") or atsai_raw.get("joinDate", ""),
        "offerLetterRef":       (
            profile.get("offerLetterRef") or
            atsai_raw.get("offer_letter_ref_no", "")
        ),
        "reportingTo":          reporting_to,
        "status":               profile.get("status", "Active"),
        "ndaSigned":            profile.get("ndaSigned", False),
        "ndaSignedAt":          profile.get("ndaSignedAt", ""),
        "assessmentScore":      assessment_score,
        "assessmentFeedback":   (
            profile.get("assessmentFeedback") or
            atsai.get("assessment", {}).get("feedback", "")
        ),
        "skills":               skills,
        "certifications":       certifications,
        "github":               github,
        "linkedin":             linkedin,
        "summary":              summary,
        "profileImage":         profile.get("profileImage", ""),
        "priorProjects":        prior_projects,
    }


async def seed_one(db, raw):
    # skip non-employee files like _manifest.json
    if "profile" not in raw:
        print("  Skipping — no 'profile' key found")
        return

    profile = normalize_profile(raw["profile"])
    uid     = profile.get("uid")

    if not uid:
        print("  Skipping — no uid found")
        return

    print(f"\nSeeding: {uid} ({profile.get('name', 'unknown')})")

    # ── employees ─────────────────────────────────────────────
    # upsert so re-running this file for the same uid always refreshes
    # the record instead of being skipped
    result = await db["employees"].update_one(
        {"uid": uid}, {"$set": profile}, upsert=True
    )
    if result.upserted_id is not None:
        print(f"  Inserted employee: {uid}")
    else:
        print(f"  Updated existing employee: {uid}")

    # ── task_performance ──────────────────────────────────────
    if "taskPerformance" in raw:
        data = raw["taskPerformance"]
        data["uid"] = uid
        result = await db["task_performance"].update_one(
            {"uid": uid}, {"$set": data}, upsert=True
        )
        print(f"  {'Inserted' if result.upserted_id else 'Updated'} task performance: {uid}")
    else:
        print(f"  No taskPerformance data, skipping.")

    # ── raw_attendance ────────────────────────────────────────
    if "attendance" in raw:
        data = raw["attendance"]
        data["uid"] = uid
        result = await db["raw_attendance"].update_one(
            {"uid": uid}, {"$set": data}, upsert=True
        )
        print(f"  {'Inserted' if result.upserted_id else 'Updated'} attendance: {uid}")
    else:
        print(f"  No attendance data, skipping.")


        # ── notifications ───────────────────────────────
    if "notifications" in raw:
        data = raw["notifications"]
        data["uid"] = uid
        await db["notifications"].update_one(
        {"uid": uid},
        {"$set": data},
        upsert=True
    )

    # ── projects ──────────────────────────────────────────────
    result = await db["projects"].update_one(
        {"uid": uid},
        {"$set": {"uid": uid, "priorProjects": profile.get("priorProjects", [])}},
        upsert=True
    )
    print(f"  {'Inserted' if result.upserted_id else 'Updated'} projects: {uid}")


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db     = client[DB_NAME]

    files = list(Path(DATA_FOLDER).glob("*.json"))
    if not files:
        print("No JSON files found in data/ folder.")
        return

    print(f"Found {len(files)} file(s)")

    for file in files:
        print(f"\nProcessing: {file.name}")
        try:
            with open(file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            await seed_one(db, raw)
        except Exception as e:
            print(f"  ERROR processing {file.name}: {e}")
            continue

    client.close()
    print("\nAll done.")


if __name__ == "__main__":
    asyncio.run(seed())