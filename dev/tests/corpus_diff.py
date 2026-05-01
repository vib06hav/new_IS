import json
import sys

from tests.corpus_harness import diff_corpus_versions


def main() -> int:
    version_a = sys.argv[1] if len(sys.argv) > 1 else "v1"
    version_b = sys.argv[2] if len(sys.argv) > 2 else "v2"
    diffs = diff_corpus_versions(version_a, version_b)
    print(json.dumps(diffs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
