"""PawPal+ logic layer: Task, Pet, Owner, and Scheduler (plus JSON persistence)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

FREQUENCY_DAYS = {"daily": 1, "weekly": 7}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_WEIGHT = {"high": 30, "medium": 20, "low": 10}


def to_minutes(hhmm: str) -> int:
    """Convert an 'HH:MM' string to minutes since midnight."""
    parsed = datetime.strptime(hhmm, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def to_hhmm(minutes: int) -> str:
    """Convert minutes since midnight to an 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str  # "HH:MM" 24-hour format
    frequency: str = "once"  # "once", "daily", or "weekly"
    due_date: date = field(default_factory=date.today)
    priority: str = "medium"  # "high", "medium", or "low"
    duration_minutes: int = 30
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Validate the time string, frequency, priority, and duration."""
        datetime.strptime(self.time, "%H:%M")  # raises ValueError if malformed
        if self.frequency not in ("once", *FREQUENCY_DAYS):
            raise ValueError(f"Unknown frequency: {self.frequency}")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"Unknown priority: {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def start_minutes(self) -> int:
        """Start time as minutes since midnight."""
        return to_minutes(self.time)

    @property
    def end_minutes(self) -> int:
        """End time as minutes since midnight."""
        return self.start_minutes + self.duration_minutes

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task done and return the next occurrence if it recurs."""
        self.completed = True
        days = FREQUENCY_DAYS.get(self.frequency)
        if days is None:
            return None
        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            due_date=self.due_date + timedelta(days=days),
            priority=self.priority,
            duration_minutes=self.duration_minutes,
            pet_name=self.pet_name,
        )

    def to_dict(self) -> dict:
        """Serialize this task to a JSON-friendly dict."""
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority,
            "duration_minutes": self.duration_minutes,
            "completed": self.completed,
            "pet_name": self.pet_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a task from a dict produced by to_dict()."""
        return cls(
            description=data["description"],
            time=data["time"],
            frequency=data.get("frequency", "once"),
            due_date=date.fromisoformat(data["due_date"]),
            priority=data.get("priority", "medium"),
            duration_minutes=data.get("duration_minutes", 30),
            completed=data.get("completed", False),
            pet_name=data.get("pet_name", ""),
        )

    def __str__(self) -> str:
        """Return a one-line readable summary."""
        status = "done" if self.completed else "pending"
        return (f"{self.time} | {self.pet_name or '-'} | {self.description} "
                f"[{self.frequency}, {self.priority}, {self.duration_minutes}m, {status}]")


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def pending_tasks(self) -> List[Task]:
        """Return tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def to_dict(self) -> dict:
        """Serialize this pet and its tasks."""
        return {"name": self.name, "species": self.species, "age": self.age,
                "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a pet (and its tasks) from a dict."""
        pet = cls(data["name"], data["species"], data.get("age", 0))
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        for t in pet.tasks:
            t.pet_name = pet.name
        return pet


@dataclass
class Owner:
    """A person who owns one or more pets."""

    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name (case-insensitive)."""
        return next((p for p in self.pets if p.name.lower() == name.lower()), None)

    def all_tasks(self) -> List[Task]:
        """Return every task across all pets."""
        return [t for p in self.pets for t in p.tasks]

    def to_dict(self) -> dict:
        """Serialize this owner, pets, and tasks."""
        return {"name": self.name, "pets": [p.to_dict() for p in self.pets]}

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an owner from a dict."""
        return cls(data["name"], [Pet.from_dict(p) for p in data.get("pets", [])])

    def save_to_json(self, path: str) -> None:
        """Write this owner's data to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: str) -> "Owner":
        """Load an owner from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class Scheduler:
    """Retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for one owner."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks for the owner."""
        return self.owner.all_tasks()

    # ---- Core algorithms -------------------------------------------------
    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by date, then HH:MM, then priority."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.due_date, t.time, PRIORITY_ORDER[t.priority]))

    def filter_tasks(self, pet_name: Optional[str] = None,
                     completed: Optional[bool] = None) -> List[Task]:
        """Filter tasks by pet name and/or completion status."""
        result = self.get_all_tasks()
        if pet_name is not None:
            result = [t for t in result if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        return result

    def get_todays_schedule(self, today: Optional[date] = None) -> List[Task]:
        """Return today's pending tasks in time order."""
        today = today or date.today()
        due = [t for t in self.filter_tasks(completed=False) if t.due_date == today]
        return self.sort_by_time(due)

    def detect_conflicts(self) -> List[str]:
        """Return warnings for pending tasks sharing the exact same date and time."""
        slots: Dict[tuple, List[Task]] = {}
        for t in self.filter_tasks(completed=False):
            slots.setdefault((t.due_date, t.time), []).append(t)
        warnings = []
        for (day, time), group in sorted(slots.items()):
            if len(group) > 1:
                names = ", ".join(f"{t.pet_name}: {t.description}" for t in group)
                warnings.append(f"Conflict on {day} at {time} -> {names}")
        return warnings

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Complete a task and schedule its next occurrence for recurring tasks."""
        pet = self.owner.get_pet(task.pet_name)
        next_task = task.mark_complete()
        if next_task is not None and pet is not None:
            pet.add_task(next_task)
        return next_task

    # ---- Stretch: advanced scheduling -----------------------------------
    def detect_overlaps(self) -> List[str]:
        """Return warnings for pending tasks whose time ranges overlap on the same day."""
        by_day: Dict[date, List[Task]] = {}
        for t in self.filter_tasks(completed=False):
            by_day.setdefault(t.due_date, []).append(t)
        warnings = []
        for day, group in sorted(by_day.items()):
            group.sort(key=lambda t: t.start_minutes)
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    if b.start_minutes >= a.end_minutes:
                        break  # sorted by start, so no later task can overlap a
                    warnings.append(
                        f"Overlap on {day}: {a.pet_name} '{a.description}' "
                        f"({a.time}-{to_hhmm(a.end_minutes)}) overlaps {b.pet_name} "
                        f"'{b.description}' ({b.time}-{to_hhmm(b.end_minutes)})")
        return warnings

    def find_next_available_slot(self, duration_minutes: int, day: Optional[date] = None,
                                 earliest: str = "07:00", latest: str = "21:00") -> Optional[str]:
        """Return the first 'HH:MM' start with a free gap of the given length, or None."""
        day = day or date.today()
        busy = sorted((t.start_minutes, t.end_minutes)
                      for t in self.filter_tasks(completed=False) if t.due_date == day)
        cursor, limit = to_minutes(earliest), to_minutes(latest)
        for start, end in busy:
            if start - cursor >= duration_minutes:
                break
            cursor = max(cursor, end)
        return to_hhmm(cursor) if limit - cursor >= duration_minutes else None

    def sort_by_weighted_priority(self, today: Optional[date] = None,
                                  tasks: Optional[List[Task]] = None) -> List[Task]:
        """Rank pending tasks by priority weight plus an overdue boost, then by time."""
        today = today or date.today()
        tasks = self.filter_tasks(completed=False) if tasks is None else tasks

        def score(t: Task) -> int:
            overdue_days = max((today - t.due_date).days, 0)
            return PRIORITY_WEIGHT[t.priority] + 15 * min(overdue_days, 3)

        return sorted(tasks, key=lambda t: (-score(t), t.due_date, t.time))
