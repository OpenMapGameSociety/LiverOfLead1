# How to use Claude Code

1. Go to [OpenRouter](https://openrouter.ai/) and create an API Key (don''t forget to save it somewhere, you won't be able to see it again)
2. Go to [Free Claude Code](https://github.com/Alishahryar1/free-claude-code) and follow instructions
3. Launch `fcc-server` and add the API key to the `OpenRouter` field and click on `Apply` and `Refresh`.
4. Launch `fcc-claude` **inside the repo** to launch Claude Code in terminal mode.
5. Switch model to `nex-n2-pro:free` (Sonnet equivalent) with `/model`.
6. Enjoy!

## Beginner directions for using Claude Code

1. Start Claude Code from inside the repository folder so it can see the project files.
2. Ask Claude Code to inspect the code before making changes. For example: `Please read CLAUDE.md, README.md, and the relevant source files, then explain the best way to make this change.`
3. Use slash commands for common tasks:
   - `/init` creates or updates `CLAUDE.md` for future Claude Code sessions.
   - `/model` changes the model used by Claude Code.
   - `/usage` opens the settings dialog.
4. When Claude Code proposes a multi-file or high-impact change, review the suggested plan before approving it.
5. After Claude Code edits files, check the results with normal repo commands such as `git diff`, then build or run the project before committing.

## Creating and using skills

Claude Code skills are reusable command helpers that package instructions for a specific workflow. They are useful when you want Claude Code to follow the same steps repeatedly, such as running tests, generating reports, or performing a review.

1. Put skill files in the repository's `.claude/commands/` folder.
2. Name the file after the slash command you want. For example, `.claude/commands/test.md` creates the `/test` skill.
3. Start the file with a short description of what the skill does.
4. Add the exact commands or steps Claude Code should run.
5. Use the skill from the terminal by typing its slash command, for example `/test`.

Example `.claude/commands/test.md`:

```md
# Run project tests

Run the project's test suite and report the result.

1. Run `scons target=template_debug platform=windows arch=x86_64 precision=double`.
2. Run any available test commands from `CLAUDE.md`.
3. Summarize failures and suggest the next fix.
```

Skills are best for repeatable workflows. For one-off tasks, ask Claude Code directly in natural language.
