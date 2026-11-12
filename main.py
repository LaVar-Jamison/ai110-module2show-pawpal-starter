"""CLI demo for PawPal+: sorting, filtering, recurrence, conflicts, overlaps, slots, persistence."""

import os
import sys
import tempfile
from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

# Emoji need UTF-8; Windows consoles often default to a legacy code page.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def print_schedule(title: str, tasks) -> None:
    """Print a titled, aligned table of tasks with emoji status markers."""
    print(f"\n📋 {title}")
    if not tasks:
        print("   (nothing scheduled)")
        return
    print(f"   {'':2} {'Date':<11}{'Time':<6}{'Min':<5}{'Pet':<7}{'Task':<20}{'Freq':<8}Status")
    print("   " + "-" * 66)
    for t in tasks:
        status = "✅ done" if t.completed else "⏳ pending"
        print(f"   {PRIORITY_ICON[t.priority]} {t.due_date.strftime('%a %m/%d'):<11}"
              f"{t.time:<6}{t.duration_minutes:<5}{t.pet_name:<7}{t.description:<20}"
              f"{t.frequency:<8}{status}")


def main() -> None:
    """Build a sample owner, run every scheduler feature, and print results."""
    print("🐾 PawPal+ demo")
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", age=4)
    luna = Pet("Luna", "cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order to prove sorting works.
    mochi.add_task(Task("Evening walk", "18:00", "daily", priority="medium", duration_minutes=30))
    mochi.add_task(Task("Morning walk", "07:30", "daily", priority="high", duration_minutes=45))
    luna.add_task(Task("Feed breakfast", "08:00", "daily", priority="high", duration_minutes=10))
    luna.add_task(Task("Weekly brushing", "12:00", "weekly", priority="low", duration_minutes=20))
    luna.add_task(Task("Vet meds", "07:30", "once", priority="high", duration_minutes=15))
    luna.add_task(Task("Litter box", "07:15", "daily", priority="low", duration_minutes=20,
                       due_date=date.today() - timedelta(days=2)))  # overdue

    scheduler = Scheduler(owner)

    print_schedule("Today's Schedule (sorted by time)", scheduler.get_todays_schedule())

    print("\n⚠️  Exact-time conflicts")
    for warning in scheduler.detect_conflicts() or ["No conflicts found."]:
        print(f"   {warning}")

    print("\n⚠️  Overlapping time ranges (uses task durations)")
    for warning in scheduler.detect_overlaps() or ["No overlaps found."]:
        print(f"   {warning}")

    slot = scheduler.find_next_available_slot(30)
    print(f"\n🕐 Next free 30-minute slot today: {slot}")

    print_schedule("Weighted priority ranking (priority + overdue boost)",
                   scheduler.sort_by_weighted_priority())

    print_schedule("Filter: Luna only", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna")))

    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    next_task = scheduler.mark_task_complete(walk)
    print(f"\n🔁 Completed '{walk.description}'. Next occurrence created for {next_task.due_date}.")

    print_schedule("Filter: completed tasks", scheduler.filter_tasks(completed=True))

    # Persistence round trip: save to JSON, reload, and compare.
    path = os.path.join(tempfile.gettempdir(), "pawpal_demo.json")
    owner.save_to_json(path)
    reloaded = Owner.load_from_json(path)
    same = len(reloaded.all_tasks()) == len(owner.all_tasks())
    print(f"\n💾 Saved {len(owner.all_tasks())} tasks to JSON and reloaded "
          f"{len(reloaded.all_tasks())} (match: {same}).")


if __name__ == "__main__":
    main()
