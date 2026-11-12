# HANDOFF — resume point for the software factory

**Read this file first in each new session. Then read `README.md`.** This repo has no `CLAUDE.md`.
`README.md` describes the pipeline, the files, the install steps and the commands. This file does not repeat them.

## Current state (verified 2026-11-11)

- The factory is complete as code. It follows the ZazenCodes v2 design and runs on Windows.
  - `factory/factory.py`: the only writer of `job.json`; stage rules, gate, routing, GitHub calls, merge, cost, Stop hook.
  - `.claude/skills/factory/SKILL.md`: the orchestrator.
  - `.claude/agents/`: `intake`, `spec-writer`, `builder`, `reviewer-code`, `reviewer-ux`, `reviewer-ui`,
    `reviewer-security`, `approver`.
  - `factory/dashboard.html`, `factory/config.json`, `factory/test_factory.py`.
- `python factory/test_factory.py` prints `OK: all factory checks passed`. The test uses a temporary bare repo
  and a fake `gh` program. No agent runs in the test.
- Repo: https://github.com/az9713/claude-code-software-factory (public, GPLv3). Commits: `9d95d5d` (factory),
  `a5e4dcb` (licence), then the commit that adds this file.
- The three labels exist on GitHub: `factory`, `factory:needs-info`, `factory:needs-human`.
  `python factory/factory.py status` ran against GitHub and found no labeled issue.
- **Not done: no job ran on a real issue.** The skill and the eight agents are unrun.
- Git state: branch `main`, in sync with `origin/main`. Git ignores `*.txt` and `/.ignore/`. Those are the
  user's local files (`README.txt`, `transcript_1.txt`, `transcript_2.txt`, `.ignore/software_factory.png`).
  Do not commit them.
- `az9713/software-factory` is a different, older public project. Do not push to it.

## Next task

- **Run one real job from start to end.** This repo has no project code, and `checks` in `factory/config.json`
  is `[]`, so the gate fails each job here. Do one of these first:
  1. Set `checks` here to `["python factory/test_factory.py"]`, commit, push. Then label one small issue
     `factory` and type `/factory run`. (Smallest step; recommended.)
  2. Install the factory in a project that has tests. `README.md` has the steps.
- Acceptance check: one issue goes from `intake` to `merged` or `needs-human`, and the PR exists on GitHub.
- Record each failure of the skill or of an agent prompt. Correct the prompt or the script. Add a test case to
  `factory/test_factory.py` for each script defect.
- If the user asks for something else, that takes precedence.

## Risks to check during the first run

1. **`builder` name collision.** `~/.claude/agents/02-builder.md` is also named `builder`. It is not confirmed
   which agent Claude Code spawns in this project. If the wrong agent runs, the job stops at `build` with no
   `build.md`. Correction: rename the project agent to `factory-builder` in `.claude/agents/builder.md`, in
   `next_action()` of `factory/factory.py`, in `protected_paths`, and in `SKILL.md`.
2. **Stop hook on Windows.** The command in `builder.md` is
   `python "$CLAUDE_PROJECT_DIR/factory/factory.py" hook || exit 0`. If the variable does not expand, the hook
   does nothing. The gate still decides. The hook signals a failure with JSON `{"decision": "block"}` on stdout.
3. **`agent-browser` is not installed.** `reviewer-ux`, `reviewer-ui` and the builder read code only.
   `npm install -g agent-browser` is the user's decision. It is not tested on Windows.
4. **Haiku reviewers** (`reviewer-code` at low risk, `reviewer-ui`). The video author says a weaker reviewer
   can send good work back. If that occurs, change `routing` in `factory/config.json`.
5. **Prices** in `factory/config.json` come from the author's table for `claude-fable-5-1`. They are not
   verified. The cost code read only a synthetic transcript.
6. **Fable intake** can bill to usage credits (the author's `INSTALL.md` says so).
7. A `checks` command that leaves untracked files makes the job stop with "uncommitted changes".
   `cmd.exe` runs the checks, so single quotes do not quote.

## Known differences from the v2 video (deliberate)

- The checks are a list in `factory/config.json`, not `checks.sh`.
- The script pushes the branch and opens the draft PR. The builder has no GitHub access.
- Each round spawns a new builder. There is no `SendMessage` resume.
- The script does not detect an author's answer on GitHub. Give the answer with `/factory`.

## Where to read things

- `README.md`: pipeline, files, install, commands, references to the two videos and the v2 source.
- `.claude/skills/factory/SKILL.md`: the orchestrator loop.
- Docstring of `factory/factory.py`: all script commands.
- v2 source (GPLv3): https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code-v2

## Workflow provenance and evidence

- Sources read on 2026-11-11: 362 video frames (one for each 10 s), two full transcripts, the v1 and v2
  source code.
- Skills used: `asd-ste100` (reply style), `handoff-after-clear` (this file). No other skill was used.
- Findings from the videos that shaped the design:
  - v1 failed on camera at the local merge, because the factory edited a tracked file in the main checkout.
    This factory does not touch the main checkout.
  - The filmed v2 install protected `tests/*`, and that stopped a job. Do not add tests to `protected_paths`.
  - v2 as published does not run on Windows (`import fcntl`, `chmod +x`, `lsof`).
- An earlier local version (no GitHub, fast-forward merge) existed in this session only. It was overwritten
  and never committed.

## Session-transient scratch

- The session scratchpad held the video frames, the transcripts and a clone of the v2 source. It is not
  needed. To get the v2 source again, clone the URL above. To get a transcript again, use
  `youtube_transcript_api` on video ids `ctoaIC4LHmI` and `RiaTyJ2POVo`.

## How to work

- Write replies in ASD-STE100 (the user's global rule).
- Run `python factory/test_factory.py` after each change to `factory/factory.py`.
- Commit and push only when the user asks. Stage explicit paths.
