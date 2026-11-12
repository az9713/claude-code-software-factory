# HANDOFF — resume point for the software factory

**Read this file first in each new session. Then read `README.md`.** This repo has no `CLAUDE.md`.
`README.md` describes the pipeline, the files, the install steps and the commands. This file does not repeat them.

## Current state (verified 2026-11-11, third session)

- The factory is complete as code and **ran one real job from start to end**. It follows the ZazenCodes v2
  design and runs on Windows.
- Repo: https://github.com/az9713/claude-code-software-factory (public, GPLv3). `HEAD` = `origin/main` after the
  commit that adds this file. Commits of this session:
  - `d594e9e` sets `"checks": ["python factory/test_factory.py"]` in `factory/config.json` (message has the typo "factor").
  - `39592a2` the factory's fix, and `3f192c9` the merge of PR #2.
  - `b742351` `SKILL.md`: run `step` and `approve` with Bash timeout 600000, and do not run `step` again while
    a call runs in the background.
- `python factory/test_factory.py` prints `OK: all factory checks passed`.
- Git ignores `*.txt`, `/.ignore/`, `/factory/jobs/` and `/.worktrees/`. `issue-body.md` is untracked on purpose:
  the user keeps it as the record of the issue #1 text. Do not commit it unless the user asks.
- `az9713/software-factory` is a different, older public project. Do not push to it.

### Job 001: result of the first real run (2026-11-11)

- Issue #1 "Dashboard drawer does not refresh": a real defect. `poll()` in `factory/dashboard.html` updated only
  the title of an open drawer, not the file list and the file text. Body: `issue-body.md`.
- Moves: intake ACCEPT (risk low, surface ui) -> spec -> build round 1 (`39592a2`) -> gate PASS 49 s ->
  review code=haiku, ux=sonnet, ui=haiku, all PASS, no findings -> approver APPROVE -> merge gate PASS 45 s
  -> PR #2 merged, issue #1 closed, worktree removed.
- 20 minutes, $2.06 (API price from the unverified table; not a bill on a subscription; orchestrator excluded).
- The orchestrator ran in a separate Claude Code session named `test_factory`. The job files are in
  `factory/jobs/001-dashboard-drawer-does-not/` (git-ignored, local only).
- Review notes, not defects: `refresh(j)` has no `.catch`; a text change clears a text selection in the drawer;
  the drawer has no ARIA marks for the selected file.

### Risks closed by job 001

- `builder` name collision: the project agent ran, not `~/.claude/agents/02-builder.md`. No rename needed.
- Gate time: 45-49 s in the worktree. A run from the main checkout took more than 120 s once.
- Port allocation: the builder used port 5110 (base 5100 + 10 x job 1).
- `agent-browser` is not installed. The reviewers read code only. The builder found a global
  `playwright@1.63.0` and ran page checks with it in headless Chromium. This was not designed; it worked.
- Haiku reviewers gave no false CHANGES on this job.

### Paths that have not run on a real job

1. Gate FAIL, and the round that follows it.
2. A CHANGES verdict, and round 2.
3. ESCALATE -> `needs-human`, then `approve` or `reject`.
4. NEEDS-INFO -> `needs-info`, then `feedback`.
5. The builder Stop hook on Windows. It fires only when the checks fail in the builder's worktree. No evidence
   either way from job 001.
6. Spending all `max_rounds` (3) -> `needs-human`.

## Next task (the user chose task A on 2026-11-11)

- **Test the failure paths with one small issue for each path.** Use the same procedure as job 001:
  1. The user creates the issue with `gh issue create --label factory --title "..." --body-file <file>`.
     Give the body as a file. A multi-line paste in Git Bash broke the command two times.
  2. `python factory/factory.py status` shows `new`.
  3. The user types `/factory run` in a **separate** Claude Code session in this folder.
  4. Watch from this session: a Monitor loop that reads `factory/jobs/<job>/job.json` every 5 s and prints each
     change of stage. Do not send messages to the orchestrator session.
- Suggested issues (proposals, not tested). Each one must be realistic:
  - **ESCALATE**: "Add a GitHub Actions workflow that runs `python factory/test_factory.py` on push." The approver
    escalates a CI change. Then test `approve` or `reject`.
  - **NEEDS-INFO**: a vague request, for example "The dashboard is hard to read." Then answer with `/factory <answer>`.
  - **Gate FAIL on a protected path**: a request whose fix must edit `factory/config.json` or `factory/factory.py`,
    for example "Lower the default `concurrency` to 2." Intake can reject it, or the gate fails each round. Either
    result is information.
  - **CHANGES / Stop hook**: no deterministic trigger is known. Record them if they occur on another job.
- Tell the user before each run: the issue and PR are public, and APPROVE merges into `main` with no human check.
- Acceptance check: each tested path ends in its expected stage, and the script and agents behave as `SKILL.md`
  says. Record each failure of a prompt or the script. Correct it. Add a test case to `factory/test_factory.py`
  for each script defect.
- Backup task B: install the factory in a real project that has tests (`README.md` has the steps).
- If the user asks for something else, that takes precedence.

## Remaining risks

1. **Prices** in `factory/config.json` come from the author's table for `claude-fable-5-1`. Not verified.
2. **Fable intake** can bill to usage credits (the author's `INSTALL.md` says so).
3. A `checks` command that leaves untracked files makes the job stop with "uncommitted changes". `cmd.exe` runs
   the checks, so single quotes do not quote.
4. The gate here runs only the factory self-check. It does not test `factory/dashboard.html`. Reviewers and the
   approver judge dashboard changes.

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

- Sessions 1 and 2 (2026-11-11): built the factory from 362 video frames, two transcripts and the v1 and v2
  source; gave the user test steps. Skills used: `asd-ste100` (reply style), `handoff-after-clear`.
- Session 3 (2026-11-11): guided the user through job 001 step by step, watched it from disk, fixed the gate
  timeout in `SKILL.md`. Skills used: `handoff-after-clear` (this file). The `factory` skill ran in the
  `test_factory` session, not in this one. `asd-ste100` applies through the user's global rule.
- Evidence: `gh pr list --state all` shows PR #2 `MERGED` at 2026-11-12T06:39:42Z (UTC). `gh issue list` shows
  #1 `CLOSED`. `factory.py status` shows job 001 `done`, `merged`, round 1/3, $2.06, 20 min.
- Findings from the videos that shaped the design:
  - v1 failed on camera at the local merge, because the factory edited a tracked file in the main checkout.
    This factory does not touch the main checkout. Job 001 confirmed it.
  - The filmed v2 install protected `tests/*`, and that stopped a job. Do not add tests to `protected_paths`.
  - v2 as published does not run on Windows (`import fcntl`, `chmod +x`, `lsof`).

## Session-transient scratch

- The builder's Playwright script `drawer-check.js` and its fixture `factory/jobs/900-drawer-test-5110/` lived in
  that builder's scratchpad and worktree. Both are gone. `build.md` of job 001 describes the method.
- To get the v2 source again, clone the URL above. To get a transcript again, use `youtube_transcript_api` on
  video ids `ctoaIC4LHmI` and `RiaTyJ2POVo`.

## How to work

- Write replies in ASD-STE100 (the user's global rule).
- Run `python factory/test_factory.py` after each change to `factory/factory.py`.
- Commit and push only when the user asks. Stage explicit paths.
- Read job worktrees with `git -C .worktrees/<job> ...`. Do not `cd` into `.worktrees/`: the session's working
  folder moves there, and the script deletes that folder at the merge.
