---
name: hoi-clean-artifacts
description: Lists and optionally removes LiverOfLead1 build artifacts.
disable-model-invocation: true
allowed-tools:
  - Bash(find *)
  - Bash(du *)
  - Bash(rm *)
  - Bash(git status *)
---

# /hoi-clean-artifacts

List and optionally remove local build artifacts for LiverOfLead1.

## Safety rules

Never delete:

- `.git/`
- `.claude/`
- `src/`
- `project/*.gd`
- `project/*.tscn`
- `project/*.gdextension`
- `project/bin/*.gdextension`
- `godot-cpp/`
- `doc/`
- documentation files
- any file the user did not explicitly approve
- no need to use Python

## Workflow

1. Run from the repository root.
2. List likely artifact candidates:

   ```text
   bin/
   build/
   cmake-build*/
   .sconsign*.dblite
   compile_commands.json
   src/gen/
   *.o
   *.os
   *.so
   *.obj
   *.bc
   *.pyc
   project/bin/linux/
   project/bin/windows/
   project/bin/macos/
   ```

3. Show the candidate list to the user.
4. Ask for explicit confirmation before deleting anything.
5. After confirmation, delete only the approved candidates.
6. Run `git status --short` afterward and report what changed.

## Current status and likely artifacts

!`git status --short`
!`find . \( -path './.git' -o -path './godot-cpp/.git' \) -prune -o \( -name 'bin' -o -name 'build' -o -name 'cmake-build*' -o -name '.sconsign*.dblite' -o -name 'compile_commands.json' -o -path './src/gen' -o -name '*.o' -o -name '*.os' -o -name '*.so' -o -name '*.obj' -o -name '*.bc' -o -name '*.pyc' -o -path './project/bin/linux' -o -path './project/bin/windows' -o -path './project/bin/macos' \) -print`
