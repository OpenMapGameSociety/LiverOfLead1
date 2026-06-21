---
name: lol-ci-check
description: Runs or plans the LiverOfLead1 CI-style checks.
disable-model-invocation: true
argument-hint: "[local|full|raw scons args]"
allowed-tools:
  - Bash(clang-format *)
  - Bash(scons *)
  - Bash(git status *)
---

# /lol-ci-check

Run CI-style checks for LiverOfLead1.

## Arguments

- No arguments or `local`: run the practical local CI subset.
- `full`: run the CI matrix from `.github/workflows/ci.yml`.
- Raw SCons arguments: run a single CI-style build.

## Local default

From the repository root, run:

```text
clang-format src/*.h src/*.cpp --dry-run --Werror
scons target=template_debug platform=linux arch=x86_64 precision=double
```

## Full CI matrix

Only run the full matrix if the user explicitly asks for `full`.

The matrix in `.github/workflows/ci.yml` is:

```text
scons target=template_debug platform=linux arch=x86_64 precision=double
scons target=template_release platform=windows arch=x86_64 precision=single
scons target=template_debug platform=macos arch=universal precision=single
scons target=template_debug platform=android arch=arm64 precision=single
scons target=template_release platform=web arch=wasm32 precision=double
```

Do not run cross-platform builds that the local machine cannot support. If a target is unavailable, say which command was skipped and why.

## Raw SCons arguments

If the user provides raw SCons arguments, run:

```text
scons $ARGUMENTS
```

## Reporting

Report each command, pass/fail status, and any artifact path found under `project/bin/<platform>/`.

## Current status

!`git status --short`
