# Contributing

## Start here

The live implementation record is [`PROJECT_STATUS.md`](PROJECT_STATUS.md).
It—not this file—is updated after every material implementation. Read its
**Current focus**, **Next implementation queue**, and **Current blockers** before
starting work. Update it in the same commit whenever an implementation changes
the project state or next step.

## Development workflow

1. Keep each change focused and traceable. The current owner-operated workflow
   commits approved changes directly to `main`; outside contributors use a
   focused branch and pull request.
2. Add or update tests for behavioral changes.
3. Run `make check` before committing or opening a pull request.
4. For study-protocol changes, also run `make plan-validate`.
5. Use professional, outcome-oriented commit messages and include the status
   update with its implementation.
6. Do not include real patient or controlled-access data in issues, commits,
   logs, screenshots, tests, or pull requests.
