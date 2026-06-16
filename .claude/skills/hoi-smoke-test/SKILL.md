---
name: hoi-smoke-test
description: Runs the HeartsofOpenIron local smoke test: formatting plus Linux debug build.
disable-model-invocation: true
allowed-tools:
  - Bash(clang-format *)
  - Bash(scons *)
  - Bash(test *)
  - Bash(find *)
  - Bash(git status *)
---

# /hoi-smoke-test

Run the fast local validation flow for HeartsofOpenIron.

## Workflow

Run these steps in order from `/home/alexandre/Documents/HeartsofOpenIron`:

1. Check C++ formatting:

   ```text
   clang-format src/*.h src/*.cpp --dry-run --Werror
   ```

2. Build the default Linux debug GDExtension:

   ```text
   scons target=template_debug platform=linux arch=x86_64 precision=double
   ```

3. Check that a built library exists under `project/bin/linux/`.
4. Stop at the first failure and report the failing command.
5. If all steps pass, report the formatting result and artifact path.

## Current status

!`git status --short`
