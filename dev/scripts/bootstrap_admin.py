import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.auth.service import bootstrap_admin_user
from app.config import settings
from app.database import SessionLocal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or promote a local admin access record for founder/bootstrap onboarding.",
    )
    parser.add_argument("--name", required=True, help="Admin display name")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument(
        "--password",
        default="ignored",
        help="Deprecated compatibility flag. Local passwords are no longer used.",
    )
    parser.add_argument(
        "--promote-existing",
        action="store_true",
        help="Promote an existing non-admin user with this email to admin",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Deprecated compatibility flag retained for older bootstrap workflows.",
    )
    parser.add_argument(
        "--allow-non-dev",
        action="store_true",
        help="Allow running outside development when you intentionally need a manual bootstrap",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if settings.APP_ENV != "development" and not args.allow_non_dev:
        parser.error("Refusing to bootstrap an admin outside development without --allow-non-dev")

    db = SessionLocal()
    try:
        user, action = bootstrap_admin_user(
            db,
            name=args.name,
            email=args.email,
            password=args.password,
            promote_existing=args.promote_existing,
            reset_password=args.reset_password,
        )
    except Exception as exc:
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Admin {action}: {user.email} ({user.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
