"""Run Quarto with the release calendar belonging to the selected profile."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path


STUDENT = "student"
INSTRUCTOR = "instructor"
PROFILES = (STUDENT, INSTRUCTOR)


class ScheduleSelectionError(RuntimeError):
    """Raised when a schedule cannot be selected safely."""


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ScheduleSelection:
    """Serialize renders and temporarily select the instructor schedule."""

    def __init__(self, root: Path, profile: str) -> None:
        self.root = root
        self.profile = profile
        self.state_dir = root / ".quarto" / "schedule-selection.lock"
        self.backup = self.state_dir / "student-schedule.yml"
        self.student_schedule = root / "_schedule.yml"
        self.instructor_schedule = root / "_schedule-instructor.yml"
        self._locked = False

    def _recover_or_reject_existing_lock(self) -> None:
        if not self.state_dir.exists():
            return

        owner_file = self.state_dir / "owner.json"
        try:
            owner = json.loads(owner_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            owner = {}

        same_host = owner.get("hostname") == socket.gethostname()
        owner_alive = same_host and _process_is_alive(int(owner.get("pid", -1)))
        if owner_alive:
            raise ScheduleSelectionError(
                f"Another profile render is active (PID {owner['pid']})."
            )

        if self.backup.exists():
            os.replace(self.backup, self.student_schedule)
        shutil.rmtree(self.state_dir)

    def __enter__(self) -> "ScheduleSelection":
        if self.profile not in PROFILES:
            raise ScheduleSelectionError(f"Unknown profile: {self.profile}")
        if not self.student_schedule.is_file():
            raise ScheduleSelectionError(f"Missing student schedule: {self.student_schedule}")
        if self.profile == INSTRUCTOR and not self.instructor_schedule.is_file():
            raise ScheduleSelectionError(
                f"Missing instructor schedule: {self.instructor_schedule}"
            )

        self.state_dir.parent.mkdir(parents=True, exist_ok=True)
        self._recover_or_reject_existing_lock()
        try:
            self.state_dir.mkdir()
        except FileExistsError as error:
            raise ScheduleSelectionError("Another profile render started concurrently.") from error

        self._locked = True
        (self.state_dir / "owner.json").write_text(
            json.dumps({"pid": os.getpid(), "hostname": socket.gethostname()}),
            encoding="utf-8",
        )

        if self.profile == INSTRUCTOR:
            shutil.copyfile(self.student_schedule, self.backup)
            replacement = self.state_dir / "active-schedule.yml"
            shutil.copyfile(self.instructor_schedule, replacement)
            os.replace(replacement, self.student_schedule)

        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        try:
            if self.profile == INSTRUCTOR and self.backup.exists():
                os.replace(self.backup, self.student_schedule)
        finally:
            if self._locked:
                shutil.rmtree(self.state_dir, ignore_errors=True)
                self._locked = False


def run_quarto(root: Path, command: str, profile: str) -> int:
    with ScheduleSelection(root, profile):
        completed = subprocess.run(
            ["quarto", command, "--profile", profile],
            cwd=root,
            check=False,
        )
    return completed.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("render", "preview", "render-all"))
    parser.add_argument("profile", nargs="?", choices=PROFILES)
    args = parser.parse_args(argv)
    if args.command != "render-all" and args.profile is None:
        parser.error("render and preview require a profile")
    if args.command == "render-all" and args.profile is not None:
        parser.error("render-all does not accept a profile")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parent.parent
    try:
        if args.command == "render-all":
            student_result = run_quarto(root, "render", STUDENT)
            if student_result != 0:
                return student_result
            return run_quarto(root, "render", INSTRUCTOR)
        return run_quarto(root, args.command, args.profile)
    except ScheduleSelectionError as error:
        print(f"Schedule selection failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
