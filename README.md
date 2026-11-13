# Software factory

A software factory for Claude Code that runs on Windows. It takes GitHub issues that have the `factory` label
and turns each issue into a pull request. Agents do the judgment. One Python script does the work that must be
deterministic.

## References

This project follows the two software factory videos by ZazenCodes:

- [Build Your Own AI Software Factory with Claude Code](https://www.youtube.com/watch?v=ctoaIC4LHmI) (v1)
- [Build a Better Software Factory with Claude Code](https://www.youtube.com/watch?v=RiaTyJ2POVo) (v2)

The design, the stage names, the routing table and the cost method come from the v2 source code:
[zazencodes-season-3/src/software-factory-claude-code-v2](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code-v2).
That source has the GPLv3 licence. This repo is a derived work, so this repo also has the GPLv3 licence. See `LICENSE`.

The v2 source does not run on Windows: `factory/bin/job` imports `fcntl`, and the scripts need `chmod +x` and
`lsof`. This project is one Python file with the standard library only.

## Pipeline

```
GitHub issue with the label `factory`
  -> intake      intake (Fable): ACCEPT | NEEDS-INFO | REJECT, plus risk and surfaces; posted on the issue
  -> spec        spec-writer (Opus): spec.md
  -> build       builder (Opus): code on branch factory/<job> in .worktrees/<job>, build.md
  -> gate        the script pushes the branch, opens a draft PR "Closes #<n>", runs the checks
                 FAIL goes back to build; no reviewer starts
  -> review      reviewer-code, plus reviewer-ux, reviewer-ui, reviewer-security by risk and surfaces, in parallel
                 one CHANGES goes back to build
  -> approve     approver (Opus): APPROVE | ESCALATE
  -> merged      the script merges origin/<base> into the branch, runs the gate again, pushes, merges the PR
```

- `needs-info`: the job waits for the author of the issue.
- `needs-human`: the PR waits for you. Merge the PR on GitHub to approve it.
- A job gets a maximum of `max_rounds` build rounds (default 3). Then the job goes to `needs-human`.
- One orchestrator session runs a maximum of `concurrency` jobs at one time (default 2).

## Files

| File | Purpose |
|---|---|
| `.claude/skills/factory/SKILL.md` | The orchestrator. It spawns agents and runs the script. |
| `.claude/agents/*.md` | Eight agents: `intake`, `spec-writer`, `builder`, four reviewers, `approver`. Each agent writes one file. |
| `factory/factory.py` | The only writer of `job.json`. It holds the stage rules, the gate, the routing, the GitHub calls, the merge and the cost sum. |
| `factory/config.json` | Checks, concurrency, rounds, labels, routing, protected paths, ports, prices. |
| `factory/dashboard.html` | A read-only board of the jobs. |
| `factory/test_factory.py` | The self-check. It uses a temporary repo and a fake `gh` program. |

Runtime state is in `factory/jobs/` and `.worktrees/`. Git ignores the two folders.

## Install in a project

The project must have a GitHub `origin`, and `gh auth status` must show a user who can push.

1. Copy `.claude/skills/factory/`, the eight files in `.claude/agents/` and `factory/` into the project.
2. Set `base_branch`, `merge_method` and `checks` in `factory/config.json`. `cmd.exe` runs the checks on
   Windows, so use double quotes.
3. Add `/factory/jobs/` and `/.worktrees/` to `.gitignore`.
4. Commit the files. Push them to the base branch.
5. Run `python factory/factory.py setup`. This command creates the three labels.
6. Start Claude Code again.

## Use

```
/factory run             work through all labeled issues; also continues after a stop
/factory run <n>         work on issue <n>
/factory <feature>       create a labeled issue for the feature, then run it
/factory <other words>   a question, feedback, an approval or a rejection for a job
```

To see the dashboard, run this command, then open `http://localhost:8765/dashboard.html`:

```
python -m http.server 8765 --bind 127.0.0.1 --directory factory
```

Click "Turn on notifications" on the dashboard to get a desktop notification when a job enters `needs-human` or
`needs-info`. This works only while the dashboard page is open in a browser. A background tab is sufficient.

## Test

```
python factory/test_factory.py
```

The test makes a temporary bare repo as `origin` and walks jobs through each stage. The test writes the agent
files itself. No agent runs, and no call goes to GitHub.

The workflow `.github/workflows/self-check.yml` also runs the self-check on GitHub on each push and each pull request.

## Status

- `factory/factory.py` passes the self-check.
- The skill and the eight agents did not run on a real issue yet.
- This repo has no project code. `checks` is empty, so the gate fails each job here. Install the factory in a
  project that has tests.
- The UX and UI reviewers open pages only if `agent-browser` is installed. If it is not installed, they read
  the code.
- The cost figure is the API price of the agents of a job, from the author's price table. On a subscription
  the figure compares jobs. The figure is not a bill. The prices are not verified.
- The author of the videos gives this caution: do not connect a factory to production with no human check.
