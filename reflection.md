# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML had four classes. Task is a dataclass holding a description, a time, a frequency, and a 
completion flag, with a mark_complete() method. Pet is a dataclass holding its name, species, age, 
and a list of its tasks, and it owns adding and removing tasks. Owner holds a list of pets and can return 
every task across all of them. Scheduler is the "brain": it holds a reference to an Owner and is responsible 
retrieving and organizing tasks. I kept the relationships simple: an Owner has many Pets, a Pet has many Tasks, 
and the Scheduler reads from the Owner rather than storing its own copy of any data.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.


The design changed in three ways. First, Task gained a pet_name field, set automatically in Pet.add_task(). My first draft had no way to tell which 
pet a task belonged to once the Scheduler flattened every pet's tasks into one list, which made filtering by pet and printing a readable schedule awkward. 
Second, Task.due_date and priority were added because "today's schedule" and recurrence cannot work with a time string alone, and priority gives a sensible 
tie-breaker. Third, Task.mark_complete() now returns the next occurrence instead of returning nothing, and Scheduler.mark_task_complete() 
attaches that new task to the correct pet, so the Task never needs to know about its parent Pet.



---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers due date, time of day, priority, completion status, and frequency. Time matters most because a pet 
care schedule is fundamentally a timeline, so sorting is by date and HH:MM first. 
Priority only breaks ties between tasks at the same time. 
Completion status decides what shows up in "today's schedule" and what counts as a conflict, since finished tasks should not block anything.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The conflict detector only flags tasks scheduled for the exact same date and time. It does not consider task duration, so a 30-minute walk at 07:30 and a 
feeding at 07:45 are not flagged even though they overlap in real life. I accepted this because 
tasks in the app have no duration field, exact-match detection is a simple grouping pass that is easy to read and test, and it 
returns a warning string instead of blocking the user. For a family pet schedule, catching obvious double-bookings is the most valuable 80%, and 
adding durations would complicate both the data entry and the UI.


---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used the AI assistant for design brainstorming (turning my list of objects into a Mermaid class diagram), generating the class skeleton from that diagram, drafting the first pass of each algorithm, 
writing docstrings, and drafting the pytest suite. I used separate chat sessions for each phase (design, core implementation, algorithms, testing, polish), which kept each conversation focused and stopped earlier design discussion from cluttering later debugging. 
The most helpful prompts were specific and referenced the actual file, such as "Based on my skeletons in pawpal_system.py, how should the Scheduler retrieve all tasks from the Owner's pets?" and "What are the most important edge cases to test 
for a pet scheduler with sorting and recurring tasks?" Vague prompts produced generic code; prompts that named a file, a method, and a constraint produced code I could use.


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

N/A
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I wrote 13 tests covering: marking a task complete, adding a task to a pet, chronological sorting, priority tie-breaking, 
daily and weekly recurrence, one-time tasks not recurring, conflict detection across pets, no false conflicts for different times, 
completed tasks being ignored by conflict detection, filtering by pet and status, a pet with no tasks, and 
rejection of invalid time strings. These matter because sorting, recurrence, and conflicts are the behaviors a user 
relies on and the easiest to break silently, and the edge cases (empty pets, completed tasks) are where schedulers usually fail.



**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am about 4 out of 5 confident. All 13 tests pass and the CLI demo output matches what I expect by hand. I am less sure about behavior I did not test. 
If I had more time I would test overlapping durations, tasks that cross midnight, recurring tasks completed 
late (a daily task finished two days after its due date still schedules from the old due date), monthly recurrence, duplicate pet names, and 
Streamlit session state behavior across reruns

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with the separation between the logic layer and the UI. Because pawpal_system.py has no Streamlit code, 
I could verify everything from main.py and pytest before touching app.py, 
and the UI ended up as a thin layer that just calls Scheduler methods. Returning the next task from 
mark_complete() was also a clean decision that made recurrence easy to test.


**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would add a duration_minutes field so conflict detection can find overlapping tasks, persist data to a JSON file so it survives a browser refresh, and make recurrence schedule 
from the completion date or the due date by user choice. I would also move filtering and sorting options into one query object instead of separate method parameters.


**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Being the lead architect means the AI can write code quickly but I am responsible for the design decisions and for verifying them. The most 
habits were writing the UML first, giving the AI small, specific tasks tied to real files, and checking every suggestion against 
tests before accepting it. AI was strongest at generating boilerplate and test drafts, and weakest at knowing which tradeoffs fit my project, which only I could decide.
