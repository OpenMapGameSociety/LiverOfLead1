# LiverOfLead1 Claude Code skills

This repo includes project-local Claude Code skills under `.claude/skills/`. Invoke them with `/skill-name`.

| Skill | Command | Purpose |
| --- | --- | --- |
| Build | `/hoi-build` | Build the Godot GDExtension with SCons. Defaults to Linux debug. |
| Format check | `/hoi-format-check` | Run `clang-format --dry-run --Werror` without modifying files. |
| Format fix | `/hoi-format-fix` | Apply `clang-format -i` to C++ sources after checking the working tree. |
| Smoke test | `/hoi-smoke-test` | Run formatting check plus the default Linux debug build. |
| CI check | `/hoi-ci-check` | Run local CI-style checks or list/run the full CI matrix when requested. |
| Clean artifacts | `/hoi-clean-artifacts` | List build artifacts and delete only approved candidates. |

## Usage examples

```text
/hoi-build
/hoi-build windows-release
/hoi-build target=template_release platform=linux arch=x86_64 precision=single

/hoi-format-check
/hoi-format-fix

/hoi-smoke-test

/hoi-ci-check
/hoi-ci-check local
/hoi-ci-check full

/hoi-clean-artifacts
```

## Skill locations

- `.claude/skills/hoi-build/SKILL.md`
- `.claude/skills/hoi-format-check/SKILL.md`
- `.claude/skills/hoi-format-fix/SKILL.md`
- `.claude/skills/hoi-smoke-test/SKILL.md`
- `.claude/skills/hoi-ci-check/SKILL.md`
- `.claude/skills/hoi-clean-artifacts/SKILL.md`

## Notes

- Skills are project-local and are intended for this repository only.
- Destructive or in-place actions require explicit confirmation before files are deleted or formatted.
- The build skills use the commands documented in `CLAUDE.md`.
