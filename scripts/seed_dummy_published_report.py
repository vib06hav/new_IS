import argparse
from datetime import datetime
import json
import shutil
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.auth.security import get_password_hash
from app.config import settings
from app.database import SessionLocal
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.canonical_record import CanonicalRecord
from app.models.final_report import FinalReport
from app.models.user import User


SEED_APPLICATION_ID = UUID("11111111-1111-1111-1111-111111111111")
SEED_DISPLAY_ID = "Dummy App (5)_v8_filled"
SEED_ADMIN_EMAIL = "seed.admin@example.com"
SEED_ADMIN_PASSWORD = "SeedAdminPass123!"
SEED_INTERVIEWER_LOOKUP = "vib"
SEED_INTERVIEWER_EMAIL = "seed.interviewer@example.com"
SEED_INTERVIEWER_PASSWORD = "SeedInterviewerPass123!"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed one realistic published report for UI development.",
    )
    parser.add_argument(
        "--application-id",
        default=str(SEED_APPLICATION_ID),
        help="Application UUID to use for the seeded record.",
    )
    parser.add_argument(
        "--admin-email",
        default=SEED_ADMIN_EMAIL,
        help="Admin email to create or reuse for assignment ownership.",
    )
    parser.add_argument(
        "--admin-password",
        default=SEED_ADMIN_PASSWORD,
        help="Password to set when creating the admin seed user.",
    )
    parser.add_argument(
        "--interviewer",
        default=SEED_INTERVIEWER_LOOKUP,
        help="Existing interviewer email or display name to assign and attribute the published draft to.",
    )
    parser.add_argument(
        "--interviewer-email",
        default=SEED_INTERVIEWER_EMAIL,
        help="Fallback interviewer email to create if --interviewer does not match an existing interviewer.",
    )
    parser.add_argument(
        "--interviewer-password",
        default=SEED_INTERVIEWER_PASSWORD,
        help="Password to set when creating the fallback interviewer seed user.",
    )
    return parser


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_user(
    db,
    *,
    email: str,
    password: str,
    name: str,
    role: str,
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        changed = False
        if user.name != name:
            user.name = name
            changed = True
        if user.role != role:
            user.role = role
            changed = True
        if changed:
            db.flush()
        return user

    user = User(
        name=name,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def find_existing_interviewer(db, lookup: str) -> User | None:
    normalized = lookup.strip()
    if not normalized:
        return None

    return (
        db.query(User)
        .filter(
            User.role == "interviewer",
            (User.email == normalized) | (User.name.ilike(normalized)),
        )
        .first()
    )


def copy_source_pdf(application_id: UUID) -> str:
    source_pdf = PROJECT_ROOT / "tests" / "pdfs" / f"{SEED_DISPLAY_ID}.pdf"
    if not source_pdf.exists():
        raise FileNotFoundError(f"Seed PDF not found: {source_pdf}")

    upload_dir = Path(settings.UPLOAD_DIRECTORY)
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_pdf = upload_dir / f"{application_id}.pdf"
    shutil.copy2(source_pdf, target_pdf)
    return str(target_pdf)


def upsert_seed_application(
    db,
    *,
    application_id: UUID,
    admin_user: User,
    interviewer_user: User,
    file_path: str,
    display_id: str,
    canonical_data: dict,
    ros_content: dict,
) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        application = Application(
            id=application_id,
            display_id=display_id,
            uploaded_by=admin_user.id,
            file_path=file_path,
            status="ASSIGNED",
            is_hidden=False,
        )
        db.add(application)
        db.flush()
    else:
        application.display_id = display_id
        application.uploaded_by = admin_user.id
        application.file_path = file_path
        application.status = "ASSIGNED"
        application.is_hidden = False
    application.last_activity_at = datetime.utcnow()

    canonical_record = (
        db.query(CanonicalRecord)
        .filter(CanonicalRecord.application_id == application_id)
        .first()
    )
    pages_1_3 = {
        "page_1_background_profile": ros_content["page_1_background_profile"],
        "page_2_academic_and_engagement": ros_content["page_2_academic_and_engagement"],
        "page_3_essays": ros_content["page_3_essays"],
    }
    if canonical_record is None:
        canonical_record = CanonicalRecord(
            application_id=application_id,
            canonical_version=str(canonical_data.get("canonical_version", "1.1")),
            canonical_data=canonical_data,
            pages_1_3=pages_1_3,
        )
        db.add(canonical_record)
    else:
        canonical_record.canonical_version = str(canonical_data.get("canonical_version", "1.1"))
        canonical_record.canonical_data = canonical_data
        canonical_record.pages_1_3 = pages_1_3

    final_report = (
        db.query(FinalReport)
        .filter(FinalReport.application_id == application_id)
        .first()
    )
    report_version = str((ros_content.get("report_metadata") or {}).get("report_version") or "ROS_v1")
    if final_report is None:
        final_report = FinalReport(
            application_id=application_id,
            content=ros_content,
            generated_by=admin_user.id,
            report_version=report_version,
        )
        db.add(final_report)
    else:
        final_report.content = ros_content
        final_report.generated_by = admin_user.id
        final_report.report_version = report_version

    assignment = db.query(Assignment).filter(Assignment.application_id == application_id).first()
    if assignment is None:
        assignment = Assignment(
            application_id=application_id,
            interviewer_id=interviewer_user.id,
            assigned_by=admin_user.id,
        )
        db.add(assignment)
    else:
        assignment.interviewer_id = interviewer_user.id
        assignment.assigned_by = admin_user.id
    assignment.is_hidden_for_interviewer = False

    db.flush()
    return application


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    application_id = UUID(args.application_id)

    canonical_path = PROJECT_ROOT / "tests" / "pipeline_stages" / "11_canonical_assembled.json"
    ros_path = PROJECT_ROOT / "tests" / "stage17_fake_llm_output" / "09_final_ros.json"
    canonical_data = load_json(canonical_path)
    ros_content = load_json(ros_path)
    file_path = copy_source_pdf(application_id)

    db = SessionLocal()
    seeded_application_id = str(application_id)
    seeded_interviewer_label = ""
    try:
        admin_user = ensure_user(
            db,
            email=args.admin_email,
            password=args.admin_password,
            name="Seed Admin",
            role="admin",
        )
        interviewer_user = find_existing_interviewer(db, args.interviewer)
        if interviewer_user is None:
            interviewer_user = ensure_user(
                db,
                email=args.interviewer_email,
                password=args.interviewer_password,
                name=args.interviewer,
                role="interviewer",
            )
        seeded_interviewer_label = f"{interviewer_user.name} <{interviewer_user.email}>"
        application = upsert_seed_application(
            db,
            application_id=application_id,
            admin_user=admin_user,
            interviewer_user=interviewer_user,
            file_path=file_path,
            display_id=SEED_DISPLAY_ID,
            canonical_data=canonical_data,
            ros_content=ros_content,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print("Seeded published report successfully.")
    print(f"Application ID: {seeded_application_id}")
    print(f"Admin: {args.admin_email}")
    print(f"Interviewer: {seeded_interviewer_label}")
    print(f"PDF path: {file_path}")
    print("The seeded report is visible in admin reports and interviewer application views.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
