# Rule: Generating a Code Explanation Document

## Goal

To guide an AI assistant in creating an engaging, educational explanation of completed code changes. This document should read like a senior engineer walking a colleague through their work—technical but approachable, thorough but never boring. The explanation should help future developers (and the agent itself in future tasks) understand not just _what_ was built, but _why_ decisions were made and _what was learned_ along the way.

## When to Generate

Generate this document **after completing a development task**, such as:

- Implementing a feature from a PRD
- Fixing a bug
- Refactoring code
- Setting up infrastructure or tooling

## Process

1. **Review the Completed Work:** Examine all files changed, added, or deleted during the task.
2. **Reflect on the Journey:** Consider the challenges faced, decisions made, and lessons learned.
3. **Generate Explanation:** Create the document using the structure below.
4. **Save Document:** Save as `explanation-[feature-or-task-name].md` inside the `docs/explanations/` directory.

---

## Document Structure

### 1. The Mission (Overview)

_Start with a brief, engaging summary of what was built and why it matters._

**Include:**

- What problem were we solving?
- What does the solution do at a high level?
- Why should anyone care?

**Tone:** Like you're explaining to a smart friend over coffee. Hook them in.

---

### 2. The Architecture (How It All Fits Together)

_Paint the big picture before diving into details._

**Include:**

- A visual or textual diagram of how components connect
- The "lay of the land"—where does this code live in the codebase?
- How data flows through the system
- Key abstractions and why they exist

**Use analogies liberally.** Compare your architecture to something familiar—a restaurant kitchen, a postal system, a tree's root structure. Make it stick.

---

### 3. The Codebase Tour (Structure & Organization)

_Walk through the files and folders like a tour guide._

**Include:**

- What files were created or modified?
- Why is the code organized this way?
- What does each major piece do?

**Format suggestion:**

```
📁 src/
  📁 components/
    📄 NewWidget.tsx      → The main UI component (the "face" users see)
    📄 NewWidget.test.ts  → Tests because we're not animals
  📁 hooks/
    📄 useWidgetData.ts   → Fetches and manages widget state
  📁 utils/
    📄 widgetHelpers.ts   → Pure functions for data transformation
```

---

### 4. The Technology Choices (What & Why)

_Explain the tools, libraries, and patterns used—and defend your choices._

**For each significant technology/pattern, address:**

- **What is it?** (Brief explanation for those unfamiliar)
- **Why did we choose it?** (What problem does it solve here?)
- **What alternatives did we consider?** (And why we didn't pick them)
- **Any gotchas?** (Things to watch out for)

**Example format:**

> **React Query for Server State**
>
> We chose React Query over vanilla `useEffect` + `useState` because it handles caching, background refetching, and error states out of the box. We considered Redux Toolkit Query, but React Query has a gentler learning curve and we don't need the full Redux ecosystem here.
>
> _Gotcha:_ Remember to set `staleTime` appropriately—the default of 0 means it refetches on every mount, which hammered our API during development.

---

### 5. The War Stories (Bugs, Pitfalls & Fixes)

_This is the most valuable section. Be honest about what went wrong._

**For each significant issue encountered:**

#### The Bug/Problem

Describe what happened. Be specific.

#### The Investigation

How did you figure out what was wrong? What rabbit holes did you go down?

#### The Fix

What solved it? Show code if helpful.

#### The Lesson

What should future developers (or future you) remember? How can this be avoided?

**Example:**

> ### The Mysterious Double-Submit
>
> **The Bug:** Users reported that clicking "Save" sometimes created duplicate entries.
>
> **The Investigation:** At first, I suspected a race condition in the backend. Spent an hour adding mutex locks. No dice. Then I noticed in React DevTools that the component was mounting twice. Classic React 18 Strict Mode behavior—in development, it intentionally double-mounts to help catch side effects.
>
> **The Fix:** Added a `useRef` flag to track if the submission was already in progress:
>
> ```typescript
> const isSubmitting = useRef(false);
>
> const handleSubmit = async () => {
>   if (isSubmitting.current) return;
>   isSubmitting.current = true;
>   try {
>     await submitData();
>   } finally {
>     isSubmitting.current = false;
>   }
> };
> ```
>
> **The Lesson:** When you see "impossible" duplicate behavior in React 18, check Strict Mode first. Also, always disable submit buttons during async operations—it's good UX anyway.

---

### 6. The Wisdom Gained (Best Practices & Insights)

_Share the broader lessons that transcend this specific task._

**Categories to consider:**

#### How Good Engineers Think

- What mental models helped solve this problem?
- What questions should you ask yourself when facing similar challenges?

#### Patterns Worth Repeating

- What worked well that you'd do again?
- Any reusable abstractions created?

#### Anti-Patterns to Avoid

- What would you do differently with hindsight?
- What "clever" solutions turned out to be too clever?

#### New Things Learned

- Any new technologies, APIs, or techniques discovered?
- Resources that were particularly helpful?

---

### 7. The Connections (How This Relates to Everything Else)

_Help readers understand the broader context._

**Include:**

- How does this integrate with existing systems?
- What other parts of the codebase might be affected?
- Are there related features or future work this enables?
- Dependencies: what does this rely on? What relies on this?

---

### 8. The Quick Reference (TL;DR for Future You)

_A scannable summary for when someone needs answers fast._

**Include a table or bullet list:**

| Question                      | Answer                           |
| ----------------------------- | -------------------------------- |
| Where's the main entry point? | `src/features/widget/index.ts`   |
| How do I run it locally?      | `npm run dev:widget`             |
| Where are the tests?          | `src/features/widget/__tests__/` |
| What env vars does it need?   | `WIDGET_API_KEY`, `WIDGET_ENV`   |
| Who owns this?                | @yourname, #widget-team          |

---

## Writing Guidelines

### Do:

- ✅ Write like you're explaining to a curious colleague, not a robot
- ✅ Use concrete examples and real code snippets
- ✅ Admit when something was hard or when you made mistakes
- ✅ Use analogies to explain complex concepts
- ✅ Include "why" alongside "what"
- ✅ Add humor where appropriate (but don't force it)
- ✅ Link to relevant documentation, PRs, or issues

### Don't:

- ❌ Write dry, passive voice documentation ("The function was implemented...")
- ❌ Skip over the messy parts—those are often the most educational
- ❌ Use jargon without explanation
- ❌ Assume the reader has full context
- ❌ Write a novel—be thorough but respect the reader's time
- ❌ Forget to include the "why"

---

## Output

- **Format:** Markdown (`.md`)
- **Location:** `docs/explanations/`
- **Filename:** `explanation-[feature-or-task-name].md`

---

## Example Opening

Here's how a good explanation might begin:

> # Explanation: User Notification System
>
> ## The Mission
>
> Users were missing important updates because our only notification channel was email—and let's be honest, everyone's inbox is a graveyard of unread messages. We needed a way to grab attention _inside_ the app.
>
> This implementation adds a real-time notification bell (you know the one—that little icon that makes you feel simultaneously important and anxious) that shows unread alerts, supports different notification types, and syncs across browser tabs.
>
> Think of it like adding a nervous system to our app: events happen anywhere in the body, and the brain (the user) gets a signal about what matters.

---

## Remember

The goal isn't just documentation—it's **knowledge transfer**. Write the explanation you wish you'd had before starting. Future developers (including future you) will thank you.
