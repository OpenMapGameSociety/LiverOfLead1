---
name: hoi-format-check
description: Checks C++ formatting for HeartsofOpenIron with clang-format.
disable-model-invocation: true
allowed-tools:
  - Bash(clang-format *)
  - Bash(git status *)
---

# /hoi-format-check

Check C++ formatting without modifying files.

## Workflow

1. Run from the repository root.
2. Run:

   ```text
   clang-format src/*.h src/*.cpp --dry-run --Werror
   ```

3. If `clang-format` is missing, tell the user to install it and do not modify files.
4. Report whether formatting passed.
5. If formatting failed, explain that `/hoi-format-fix` can apply the formatter.

## Current status

!`git status --short`
