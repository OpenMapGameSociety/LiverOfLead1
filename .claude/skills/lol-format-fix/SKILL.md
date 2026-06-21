---
name: lol-format-fix
description: Applies clang-format to LiverOfLead1 C++ sources.
disable-model-invocation: true
allowed-tools:
  - Bash(clang-format *)
  - Bash(git status *)
  - Bash(git diff *)
---

# /lol-format-fix

Apply C++ formatting to LiverOfLead1 sources.

## Workflow

1. Run from the repository root.
2. Before applying changes, check `git status --short`.
3. If there are unrelated uncommitted changes, ask the user whether to continue.
4. Run:

   ```text
   clang-format -i src/*.h src/*.cpp
   ```

5. Show `git diff --stat` and summarize the files changed.
6. Do not stage or commit changes unless the user asks.

## Current status

!`git status --short`
