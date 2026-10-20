"""Fail when known secret signatures exist anywhere in Git history."""

from pathlib import Path

from growthlens.history_scan import scan_git_history


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan_git_history(root)
    if findings:
        for finding in findings:
            print(f"{finding.object_sha} {finding.path}: {finding.reason}")
        return 1
    print("full Git history secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
