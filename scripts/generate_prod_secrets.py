from __future__ import annotations

import argparse
import base64
import secrets
import string


SAFE_ALPHABET = string.ascii_letters + string.digits
SAFE_ALPHABET_WITH_SYMBOLS = SAFE_ALPHABET + "_-.!@#%^+="


def random_string(length: int, alphabet: str) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_fernet_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def build_secret_map() -> dict[str, str]:
    return {
        "POSTGRES_PASSWORD": random_string(32, SAFE_ALPHABET),
        "JWT_SECRET": random_string(48, SAFE_ALPHABET_WITH_SYMBOLS),
        "WORKOS_COOKIE_PASSWORD": generate_fernet_key(),
        "MINIO_ACCESS_KEY": random_string(24, SAFE_ALPHABET),
        "MINIO_SECRET_KEY": random_string(40, SAFE_ALPHABET_WITH_SYMBOLS),
        "LLM_API_KEY_PLACEHOLDER": "<paste-provider-key-here>",
        "AICREDITS_GENERATION_API_KEY_PLACEHOLDER": "<paste-generation-key-here>",
        "AICREDITS_REPORT_CHAT_API_KEY_PLACEHOLDER": "<paste-report-chat-key-here>",
    }


def format_output(secret_map: dict[str, str], env_mode: bool) -> str:
    lines: list[str] = []
    if not env_mode:
        lines.append("Production secrets for .env.production")
        lines.append("")
        lines.append("# Copy the values below into your env file.")
        lines.append("# WORKOS_COOKIE_PASSWORD is a Fernet-compatible key.")
        lines.append("")

    for key, value in secret_map.items():
        if env_mode:
            lines.append(f"{key}={value}")
        else:
            lines.append(f"{key}={value}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate labelled production secrets for .env.production."
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Print only KEY=value lines for direct paste into an env file.",
    )
    args = parser.parse_args()

    secret_map = build_secret_map()
    print(format_output(secret_map, env_mode=args.env_only))


if __name__ == "__main__":
    main()
