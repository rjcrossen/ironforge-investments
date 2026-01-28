# Rule: Generating a Task List from User Requirements

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in Markdown format based on user requirements, feature requests, or existing documentation. The task list should guide a developer through implementation **and prompt them to document their work upon completion**.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `docs/tasks/`
- **Filename:** `tasks-[feature-name].md` (e.g., `tasks-user-profile-editing.md`)

## Process

1.  **Receive Requirements:** The user provides a feature request, task description, or points to existing documentation
2.  **Analyze Requirements:** The AI analyzes the functional requirements, user needs, and implementation scope from the provided information
3.  **Phase 1: Generate Parent Tasks:** Based on the requirements analysis, create the file and generate the main, high-level tasks required to implement the feature. **IMPORTANT: Always include task 0.0 "Create feature branch" as the first task, and the final task should always be "Generate Explanation Document"** (unless the user specifically opts out OR the change is non-code such as documentation). Use your judgement on how many additional high-level tasks to use. It's likely to be about 5. Present these tasks to the user in the specified format (without sub-tasks yet). Inform the user: "I have generated the high-level tasks based on your requirements. Ready to generate the sub-tasks? Respond with 'Go' to proceed."
4.  **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
5.  **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure sub-tasks logically follow from the parent task and cover the implementation details implied by the requirements.
6.  **Identify Relevant Files:** Based on the tasks and requirements, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including corresponding test files if applicable.
7.  **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, and notes into the final Markdown structure.
8.  **Save Task List:** Save the generated document in the `/tasks/` directory with the filename `tasks-[feature-name].md`, where `[feature-name]` describes the main feature or task being implemented (e.g., if the request was about user profile editing, the output is `tasks-user-profile-editing.md`).

## Output Format

The generated task list _must_ follow this structure:

```markdown
## Related Documents

- **PRD:** `docs/tasks/prd-[feature-name].md` - Product requirements for this feature
- **Explanation (to be created):** `docs/explanations/explanation-[feature-name].md` - Post-implementation documentation

## Relevant Files

- `path/to/potential/file1.ts` - Brief description of why this file is relevant (e.g., Contains the main component for this feature).
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - Brief description (e.g., API route handler for data submission).
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Brief description (e.g., Utility functions needed for calculations).
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:

- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 Create and checkout a new branch for this feature (e.g., `git checkout -b feature/[feature-name]`)

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 [Sub-task description 1.1]
  - [ ] 1.2 [Sub-task description 1.2]

- [ ] 2.0 Parent Task Title
  - [ ] 2.1 [Sub-task description 2.1]

- [ ] 3.0 Parent Task Title (may not require sub-tasks if purely structural or configuration)

... (additional implementation tasks)

- [ ] N.0 Generate Explanation Document
  - [ ] N.1 Review all changes made during this implementation
  - [ ] N.2 Read the explanation template at `docs/tasks/generate-explanation.md`
  - [ ] N.3 Create `docs/explanations/explanation-[feature-name].md` following the template
  - [ ] N.4 Document the architecture and how components connect
  - [ ] N.5 Document technology choices and why they were made
  - [ ] N.6 Document any bugs encountered and how they were fixed
  - [ ] N.7 Document lessons learned and best practices discovered
  - [ ] N.8 Add quick reference section with key file locations and commands
```

## Explanation Document Task Details

The final task (Generate Explanation Document) ensures that implementation knowledge is captured while it's fresh. The sub-tasks guide the agent to:

1. **Review changes** - Look at all modified/created files
2. **Follow the template** - Use `docs/tasks/generate-explanation.md` as a guide
3. **Document architecture** - Explain how pieces fit together
4. **Justify technology choices** - Explain the "why" behind decisions
5. **Capture war stories** - Document bugs, pitfalls, and fixes
6. **Share wisdom** - Record best practices and lessons learned
7. **Create quick reference** - Make it easy for future developers to get oriented

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature.

---

## Workflow Summary

The complete workflow connects three documents:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLANNING PHASE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. User provides feature request                              │
│                    ↓                                            │
│   2. Generate PRD (prd-[feature].md)                            │
│      • Clarifying questions → User answers → Final PRD          │
│                    ↓                                            │
│   3. Generate Tasks (tasks-[feature].md)                        │
│      • References the PRD                                       │
│      • Includes explanation doc as final task                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     IMPLEMENTATION PHASE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   4. Agent works through tasks                                  │
│      • Checks off completed sub-tasks                           │
│      • Notes any bugs/issues encountered                        │
│      • Records decisions made along the way                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION PHASE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   5. Generate Explanation (explanation-[feature].md)            │
│      • Follows template structure                               │
│      • Documents architecture, decisions, bugs, lessons         │
│      • Creates quick reference for future devs                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## File Locations

| Document Type           | Location             | Naming Convention               |
| ----------------------- | -------------------- | ------------------------------- |
| PRD                     | `docs/tasks/`        | `prd-[feature-name].md`         |
| Task List               | `docs/tasks/`        | `tasks-[feature-name].md`       |
| Explanation (generated) | `docs/explanations/` | `explanation-[feature-name].md` |
