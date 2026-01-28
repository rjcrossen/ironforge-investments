# Commit Message Rules

## Format (REQUIRED)

<type>(<scope>): <summary>

## Allowed Types

- feat : new user-facing feature
- fix : bug fix
- refactor : code change that does not change behavior
- test : adding or updating tests
- docs : documentation only
- chore : tooling, configs, housekeeping

## Scope

- Must reference a task ID when applicable (e.g., T-2)
- Use `core`, `api`, `ui`, or task ID
- Scope is lowercase, no spaces

## Summary Line Rules

- Max 72 characters
- Imperative mood (“add”, not “added”)
- No trailing punctuation

## Body (OPTIONAL)

Use body only if context is needed.

### Body Rules

- Wrap at 72 characters
- Explain _why_, not _what_
- Reference PRD or task IDs if relevant

## Forbidden

- Emojis
- “WIP”
- “misc”
- Vague summaries
- Multiple changes in one commit
