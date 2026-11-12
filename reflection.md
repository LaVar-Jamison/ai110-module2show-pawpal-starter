# PawPal+ Project Reflection

> **Before submitting:** the parts marked `[EDIT]` describe the design and AI process as it happened in this build. Replace any detail that does not match your own experience (especially 3b) so the reflection is specific and honest.

## 1. System Design

**Three core actions.** A user should be able to (1) add a pet, (2) schedule a care task for a pet, and (3) see today's tasks in time order with warnings for problems.

**a. Initial design**

My initial UML had four classes. `Task` is a dataclass holding a description, a time, a frequency, and a completion flag, with a `mark_complete()` method. `Pet` is a dataclass holding its name, species, age, and a list of its tasks, and it owns adding and removing tasks. `Owner` holds a list of pets and can return every task across all of them. `Scheduler` is the "brain": it holds a reference to an `Owner` and is responsible for retrieving and organizing tasks across all pets. I kept the relationships simple: an Owner has many Pets, a Pet has many Tasks, and the Scheduler reads from the Owner rather than storing its own copy of any data. `[EDIT if your first diagram differed]`

**b. Design changes**

The design changed in several ways, all reflected in `diagrams/uml_final.mmd`.
- `Task` gained a `pet_name` field, set automatically in `Pet.add_task()`. Without it, once the Scheduler flattened every pet's tasks into one list there was no way to filter by pet or print a readable schedule.
- `Task` gained `due_date` and `priority`, because "today's schedule" and recurrence cannot work from a time string alone, and priority gives a sensible tie-breaker.
- `Task.mark_complete()` now returns the next occurrence instead of nothing, and `Scheduler.mark_task_complete()` attaches it to the right pet. This keeps `Task` from needing to know about its parent `Pet`.
- For the stretch work, `Task` gained `duration_minutes` (needed for overlap detection and free-slot search), and `Task`, `Pet`, and `Owner` gained `to_dict`/`from_dict` so the whole object graph can be saved to JSON.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers due date, time of day, priority, task duration, completion status, and frequency. Time matters most because a pet care schedule is fundamentally a timeline, so the default sort is by date and `HH:MM`. Priority breaks ties between tasks at the same time. Completion status decides what shows in today's schedule and what counts as a conflict, since finished tasks should not block anything. Duration is used by the overlap checker and the free-slot search. The weighted priority ranking adds an overdue boost so that neglected tasks do not stay buried under newer high-priority ones.

**b. Tradeoffs**

The main conflict detector, `detect_conflicts()`, only flags tasks scheduled for the exact same date and time. It does not consider task duration, so a 45-minute walk at 07:30 and a feeding at 08:00 are not flagged by it even though they overlap in real life. I kept this simple version because exact-match detection is a single grouping pass that is easy to read and test, and it returns a warning string instead of blocking the user. I then added `detect_overlaps()` as a separate method rather than rewriting the first one, so the simple check stays understandable and the more thorough check is opt-in. The remaining tradeoff is that the overlap checker is a pairwise scan, which is fine for a household's worth of tasks but would need an interval tree for thousands.

---

## 3. AI Collaboration

**a. How I used AI**

I used the AI assistant for design brainstorming (turning my list of objects into a Mermaid class diagram), generating the class skeleton from that diagram, drafting the first pass of each algorithm, writing docstrings, and drafting the pytest suite. I used separate chat sessions for each phase (design, core implementation, algorithms, testing, polish), which kept each conversation focused and stopped earlier design discussion from cluttering later debugging. The most helpful prompts were specific and referenced the actual file, such as "Based on my skeletons in `pawpal_system.py`, how should the `Scheduler` retrieve all tasks from the `Owner`'s pets?" and "What are the most important edge cases to test for a pet scheduler with sorting and recurring tasks?" Vague prompts produced generic code; prompts that named a file, a method, and a constraint produced code I could use. `[EDIT to match your real usage]`

**b. Judgment and verification**

`[EDIT: replace with your own real example if yours differs.]` When I asked how to simplify the conflict detection, the AI suggested a compact version using `itertools.groupby` and a nested comprehension. It was shorter, but `groupby` requires pre-sorted input and the one-liner was hard to read, so I kept my explicit dictionary version that groups by `(date, time)`. I verified the choice by writing the conflict tests first (same time across pets, different times, completed tasks ignored) and confirming my version passed all three, then judged that readability mattered more than saving a few lines in a project where I need to explain every method. I also declined a suggestion to change `detect_conflicts()` to use durations directly, and added `detect_overlaps()` beside it instead, so the original behavior and its tests stayed stable. Finally, when emoji output was added to the CLI demo, I made sure it would not crash on a Windows console by forcing UTF-8 output, and checked the result by running the script rather than trusting that it would work.

**How correctness was verified.** Every algorithm has pytest tests for the normal case and at least one edge case, and I ran `main.py` to compare the printed schedule against what I expected by hand (for example, that the two 07:30 tasks produce a conflict and that the free slot lands in the gap before them). I also smoke-tested the Streamlit app by adding a pet and a task and confirming the data saved to JSON.

---

## 4. Testing and Verification

**a. What I tested**

I wrote 20 tests covering: marking a task complete, adding a task to a pet, chronological sorting, priority tie-breaking, daily and weekly recurrence, one-time tasks not recurring, recurrence preserving duration, conflict detection across pets, no false conflicts for different times, completed tasks being ignored, overlap detection (including back-to-back tasks not overlapping), next-free-slot search (including a full day returning `None`), weighted priority with an overdue boost, filtering by pet and status, a pet with no tasks, rejection of invalid times, and a JSON save/load round trip. These matter because sorting, recurrence, and conflicts are the behaviors a user relies on and the easiest to break silently, and the edge cases (empty pets, completed tasks, a full day) are where schedulers usually fail.

**b. Confidence**

I am about 4 out of 5 confident. All 20 tests pass and the CLI demo output matches what I expect by hand. I am less sure about behavior I did not test. With more time I would test tasks that cross midnight, recurring tasks completed late (a daily task finished two days after its due date still schedules from the old due date), monthly recurrence, duplicate pet names, a corrupted `data.json`, and Streamlit session state across reruns.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the separation between the logic layer and the UI. Because `pawpal_system.py` has no Streamlit code, I could verify everything from `main.py` and pytest before touching `app.py`, and the UI ended up as a thin layer that just calls `Scheduler` methods. Returning the next task from `mark_complete()` was also a clean decision that made recurrence easy to test.

**b. What I would improve**

I would make recurrence schedule from the completion date or the due date by user choice, let tasks span midnight, replace the pairwise overlap scan with a sorted-interval approach, and let the user edit or delete tasks from the UI. I would also move filtering and sorting options into one query object instead of separate method parameters, and store dates and times as real `datetime` objects instead of an `HH:MM` string.

**c. Key takeaway**

Being the lead architect means the AI can write code quickly but I am responsible for the design decisions and for verifying them. The most valuable habits were writing the UML first, giving the AI small, specific tasks tied to real files, and checking every suggestion against tests before accepting it. AI was strongest at generating boilerplate and test drafts, and weakest at knowing which tradeoffs fit my project, which only I could decide.

### AI strategy notes

- **Most effective features:** inline chat on a single method (for example, asking for a `lambda` key to sort `HH:MM` strings) and agent mode for multi-file changes like recurrence and persistence, which touched `Task`, `Pet`, `Owner`, `Scheduler`, `app.py`, and the tests together.
- **Rejected or modified suggestion:** see 3b. I kept the readable version over the more compact one and kept the exact-match conflict check alongside the new overlap check.
- **Separate chat sessions:** one session per phase kept context clean, so my algorithm session was not polluted by early UML debate and my testing session started from the final code.
- **Lead architect lesson:** the AI proposes, I decide, and tests are how I check.
