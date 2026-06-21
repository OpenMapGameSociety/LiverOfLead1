---
name: lol-build
description: Builds the LiverOfLead1 Godot GDExtension with SCons.
disable-model-invocation: true
argument-hint: "[linux-debug|linux-release|windows-debug|windows-release|raw scons args]"
allowed-tools:
  - Bash(scons *)
  - Bash(test *)
  - Bash(find *)
  - Bash(git status *)
---

# /lol-build

Build the LiverOfLead1 GDExtension from the repository root.

## Arguments

Use no arguments for the default local debug build:

```text
scons target=template_debug platform=linux arch=x86_64 precision=double
```

Supported shortcuts:

- `linux-debug`
- `linux-release`
- `windows-debug`
- `windows-release`

Raw SCons arguments are also supported, for example:

```text
/lol-build target=template_release platform=linux arch=x86_64 precision=single
```

If the user asks to use the example build profile, add:

```text
build_profile=build_profile.json
```

## Workflow

1. Run the build command from the repository root.
2. Use the default Linux debug command when no arguments are provided.
3. If a shortcut is provided, translate it to SCons arguments.
4. If raw SCons arguments are provided, run `scons` with the appended `ARGUMENTS` value. Do not run `scons` with an empty argument list; use the default command instead.
5. After a successful build, check for the built library under `project/bin/<platform>/` when possible.
6. Report the exact command, success/failure, and the artifact path if found.

## Current status

!`git status --short`
