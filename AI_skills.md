# LiverOfLead1 Claude Code skills

This repo includes project-local Claude Code skills under `.claude/skills/`. Invoke them with `/skill-name`.

| Skill | Command | Purpose |
| --- | --- | --- |
| Build | `/lol-build` | Build the Godot GDExtension with SCons. Defaults to Linux debug. |
| Format check | `/lol-format-check` | Run `clang-format --dry-run --Werror` without modifying files. |
| Format fix | `/lol-format-fix` | Apply `clang-format -i` to C++ sources after checking the working tree. |
| Smoke test | `/lol-smoke-test` | Run formatting check plus the default Linux debug build. |
| CI check | `/lol-ci-check` | Run local CI-style checks or list/run the full CI matrix when requested. |
| Clean artifacts | `/lol-clean-artifacts` | List build artifacts and delete only approved candidates. |

## Usage examples

```text
/lol-build
/lol-build windows-release
/lol-build target=template_release platform=linux arch=x86_64 precision=single

/lol-format-check
/lol-format-fix

/lol-smoke-test

/lol-ci-check
/lol-ci-check local
/lol-ci-check full

/lol-clean-artifacts
```

## Skill locations

- `.claude/skills/lol-build/SKILL.md`
- `.claude/skills/lol-format-check/SKILL.md`
- `.claude/skills/lol-format-fix/SKILL.md`
- `.claude/skills/lol-smoke-test/SKILL.md`
- `.claude/skills/lol-ci-check/SKILL.md`
- `.claude/skills/lol-clean-artifacts/SKILL.md`

## Notes

- Skills are project-local and are intended for this repository only.
- Destructive or in-place actions require explicit confirmation before files are deleted or formatted.
- The build skills use the commands documented in `CLAUDE.md`.
