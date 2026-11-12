"""Self-check for factory.py. Run: python factory/test_factory.py

It makes a temporary bare repo as `origin`, a clone as the main checkout, and a fake
`gh` program that keeps issues and PRs in a JSON file. The test writes the agent files
itself. No agent runs and no call goes to GitHub.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp(prefix="factory-test-")).resolve()
work, F, state = tmp / "work", tmp / "work" / "factory", tmp / "gh.json"

FAKE_GH = r'''
import json, os, subprocess, sys
P = os.environ["GH_STATE"]; S = json.load(open(P)); a = sys.argv[1:]
def opt(name, default=None): return a[a.index(name) + 1] if name in a else default
def body(): return sys.stdin.read() if opt("--body-file") == "-" else opt("--body", "")
def out(x): print(x if isinstance(x, str) else json.dumps(x))
def fresh(): return str(max(map(int, list(S["issues"]) + list(S["prs"]) + ["0"])) + 1)
kind, verb = a[0], a[1]
if kind == "api": out("operator")
elif kind == "issue" and verb == "list":
    out([{"number": int(n), "title": i["title"]} for n, i in S["issues"].items()
         if opt("--label") in i["labels"] and i["state"] == "OPEN"])
elif kind == "issue" and verb == "create":
    n = fresh()
    S["issues"][n] = {"title": opt("--title"), "body": body(), "labels": [opt("--label")], "comments": [],
                      "state": "OPEN", "author": {"login": "operator"}}
    out("https://example.test/issues/" + n)
elif kind == "issue":
    i = S["issues"][a[2]]
    if verb == "view": out(dict(i, labels=[{"name": x} for x in i["labels"]]))
    elif verb == "comment": i["comments"].append({"author": {"login": "operator"}, "body": body()})
    elif verb == "edit":
        if opt("--add-label") and opt("--add-label") not in i["labels"]: i["labels"].append(opt("--add-label"))
        if opt("--remove-label") in i["labels"]: i["labels"].remove(opt("--remove-label"))
elif kind == "pr" and verb == "create":
    n = fresh()
    S["prs"][n] = {"head": opt("--head"), "base": opt("--base"), "state": "OPEN", "draft": "--draft" in a,
                   "comments": [], "body": opt("--body")}
    out("https://example.test/pull/" + n)
elif kind == "pr":
    p = S["prs"][a[2]]
    if verb == "view": out({"state": p["state"]})
    elif verb == "ready": p["draft"] = False
    elif verb == "comment": p["comments"].append(body())
    elif verb == "close": p["state"] = "CLOSED"
    elif verb == "merge":
        if subprocess.run(["git", "push", "-q", "origin", f"{p['head']}:refs/heads/{p['base']}"]).returncode:
            sys.exit("not a fast-forward")
        p["state"] = "MERGED"
json.dump(S, open(P, "w"))
'''

ENV = dict(os.environ, FACTORY_GH=str(tmp / "fake_gh.py"), GH_STATE=str(state), CLAUDE_CONFIG_DIR=str(tmp / "cc"))


def sh(*cmd, cwd=work, stdin=""):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, input=stdin, encoding="utf-8", env=ENV)
    return r.returncode, r.stdout + r.stderr


def fac(*args, stdin=""):
    return sh(sys.executable, "factory/factory.py", *args, stdin=stdin)


def job(jid):
    return json.loads((F / "jobs" / jid / "job.json").read_text(encoding="utf-8"))


def gh_state():
    return json.loads(state.read_text(encoding="utf-8"))


def write(jid, name, text):
    p = F / "jobs" / jid / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def commit(jid, path, text, msg="work"):
    wt = Path(job(jid)["worktree"])
    (wt / path).parent.mkdir(parents=True, exist_ok=True)
    (wt / path).write_text(text, encoding="utf-8")
    assert sh("git", "add", path, cwd=wt)[0] == 0
    assert sh("git", "commit", "-m", msg, cwd=wt)[0] == 0


def build_ready(jid):
    write(jid, "build.md", f"STATUS: READY\nROUND: {job(jid)['round']}\n")


def ok(args, expect_stage, jid):
    code, out = fac(*args)
    assert code == 0, out
    assert job(jid)["stage"] == expect_stage, f"{jid} is {job(jid)['stage']}, expected {expect_stage}\n{out}"
    return out


def refused(args, word):
    code, out = fac(*args)
    assert code == 1 and word in out, f"expected a refusal with {word!r}:\n{out}"


def on_origin(path):
    sh("git", "fetch", "-q", "origin")
    return sh("git", "cat-file", "-e", f"origin/main:{path}")[0] == 0


def transcript(jid, name, model, tokens):
    """A fake subagent transcript in the place and format that Claude Code uses."""
    d = tmp / "cc" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(work)) / "session" / "subagents"
    d.mkdir(parents=True, exist_ok=True)
    folder = (F / "jobs" / jid).as_posix()
    lines = [{"type": "user", "message": {"content": f"Job: {jid}. Job folder: {folder}/. Main checkout: x."}},
             {"type": "assistant", "message": {"id": "m1", "model": model, "usage": {"input_tokens": 5}}},
             {"type": "assistant", "message": {"id": "m1", "model": model, "usage": {"input_tokens": tokens}}}]
    (d / f"agent-{name}.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return d / f"agent-{name}.jsonl"


try:
    # A repo whose checks pass unless a file named FAIL exists.
    (tmp / "fake_gh.py").write_text(FAKE_GH, encoding="utf-8")
    issue = lambda title, labels=("factory",), body="": {
        "title": title, "body": body, "labels": list(labels), "comments": [], "state": "OPEN", "author": {"login": "ann"}}
    state.write_text(json.dumps({"prs": {}, "issues": {
        "1": issue("Add alpha", body="make alpha"), "2": issue("Add beta"), "3": issue("Add gamma", labels=()),
        "4": issue("Hand merge"), "5": issue("Change alpha f"), "6": issue("Change alpha g")}}), encoding="utf-8")
    assert sh("git", "init", "-q", "--bare", "-b", "main", str(tmp / "origin.git"), cwd=tmp)[0] == 0
    assert sh("git", "clone", "-q", str(tmp / "origin.git"), str(work), cwd=tmp)[0] == 0
    F.mkdir()
    shutil.copy(HERE / "factory.py", F / "factory.py")
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    cfg.update(concurrency=2, max_rounds=2,
               checks=[f'"{sys.executable}" -c "import os,sys; sys.exit(os.path.exists(\'FAIL\'))"'])
    (F / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    (work / ".gitignore").write_text("/factory/jobs/\n/.worktrees/\n", encoding="utf-8")
    (work / "notes.txt").write_text("v1\n", encoding="utf-8")
    for c in (["checkout", "-q", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"],
              ["add", "-A"], ["commit", "-qm", "init"], ["push", "-q", "-u", "origin", "main"]):
        assert sh("git", *c)[0] == 0, c
    (work / "notes.txt").write_text("my uncommitted edit\n", encoding="utf-8")  # the factory must not touch this
    head_before = sh("git", "rev-parse", "HEAD")[1]

    # Only an open issue with the label can become a job.
    assert fac("setup")[0] == 0
    assert "new     #1" in fac("status")[1]
    refused(["create", "3"], "label")
    a = fac("create", "1")[1].strip()
    b = fac("create", "2")[1].strip()
    refused(["create", "1"], "already")
    c = fac("new", "Add delta", stdin="make delta")[1].strip()  # creates issue #7 with the label
    assert (a, b, c) == ("001-add-alpha", "002-add-beta", "003-add-delta"), (a, b, c)
    assert job(c)["issue"] == 7 and gh_state()["issues"]["7"]["body"] == "make delta"
    assert "> make alpha" in (F / "jobs" / a / "issue.md").read_text(encoding="utf-8")

    # Concurrency cap: 2 slots, the third job stays queued. `step` accepts an issue number.
    ok(["step", "1"], "intake", a)
    ok(["step", b], "intake", b)
    refused(["step", c], "concurrency")

    # Intake decides, and the decision goes on the issue. Then the spec writer, then the builder.
    refused(["step", a], "DECISION")
    write(a, "intake.md", "DECISION: ACCEPT\nRISK: low\nSURFACES: none\n\n## Summary\n- fine\n")
    out = ok(["step", a], "spec", a)
    assert "spawn spec-writer" in out and Path(job(a)["worktree"]).exists()
    assert job(a)["reviewers"] == {"code": "haiku"}
    assert "Factory intake: ACCEPT" in gh_state()["issues"]["1"]["comments"][0]["body"]
    refused(["step", a], "spec.md")
    write(a, "spec.md", "# Spec\n")
    out = ok(["step", a], "build", a)
    assert "spawn builder" in out and "Port: 5110." in out

    # Build must be written for this round and committed. The script pushes, opens a draft PR, then runs the gate.
    refused(["step", a], "build.md")
    build_ready(a)
    refused(["step", a], "no commit")
    commit(a, "alpha.txt", "alpha\n")
    out = ok(["step", a], "review", a)
    assert "spawn reviewer-code with model haiku" in out
    pr = gh_state()["prs"][str(job(a)["pr"])]
    assert pr["draft"] and pr["body"] == "Closes #1" and pr["head"] == "factory/001-add-alpha"

    # Review: a missing review refuses; CHANGES sends the job back to build, round 2.
    refused(["step", a], "no review")
    write(a, "round-1/review-code.md", "VERDICT: CHANGES\n")
    ok(["step", a], "build", a)
    assert job(a)["round"] == 2
    refused(["step", a], "build.md")  # the round-1 build.md does not count for round 2
    build_ready(a)
    ok(["step", a], "review", a)
    write(a, "round-2/review-code.md", "VERDICT: PASS\n")
    ok(["step", a], "approve", a)

    # No merge without a decision for this round. ESCALATE: PR ready, comment, label. The user approves.
    refused(["step", a], "decision.md")
    write(a, "decision.md", "DECISION: ESCALATE\nROUND: 2\n\n## For the user\nCheck alpha.\n")
    ok(["step", a], "needs-human", a)
    pr = gh_state()["prs"][str(job(a)["pr"])]
    assert not pr["draft"] and "Check alpha." in pr["comments"][0] and not on_origin("alpha.txt")
    assert "factory:needs-human" in gh_state()["issues"]["1"]["labels"]
    transcript(a, "a", "claude-opus-5-5-20261101", 1_000_000)
    ok(["approve", a], "merged", a)
    assert on_origin("alpha.txt") and not Path(job(a)["worktree"]).exists()
    assert gh_state()["prs"][str(job(a)["pr"])]["state"] == "MERGED"
    assert "factory:needs-human" not in gh_state()["issues"]["1"]["labels"]
    assert job(a)["cost_usd"] == 4.0, job(a)["cost_usd"]  # 1M opus input tokens at $4; the last record of a message counts
    refused(["step", a], "does not move")

    # Job b: ui + security surfaces route four reviewers. A failing gate never reaches review.
    write(b, "intake.md", "DECISION: ACCEPT\nRISK: high\nSURFACES: ui, security\n")
    ok(["step", b], "spec", b)
    assert job(b)["reviewers"] == {"code": "sonnet", "ux": "sonnet", "ui": "haiku", "security": "opus"}
    write(b, "spec.md", "# Spec\n")
    ok(["step", b], "build", b)
    commit(b, "FAIL", "x\n")
    build_ready(b)
    ok(["step", b], "build", b)  # gate FAIL -> round 2, not review
    assert job(b)["round"] == 2 and job(b)["rounds"]["1"]["checks"] == "FAIL"

    # The Stop hook of the builder: a JSON "block" while the checks fail, silence on input that it cannot read.
    event = json.dumps({"agent_transcript_path": str(transcript(b, "b", "claude-haiku-5-5", 1))})
    code, out = fac("hook", stdin=event)
    assert code == 0 and json.loads(out)["decision"] == "block" and "The gate will reject" in out, (code, out)
    assert fac("hook", stdin="not json") == (0, "")

    build_ready(b)
    ok(["step", b], "needs-human", b)  # round cap 2 reached
    assert "round limit" in job(b)["note"]

    # Feedback gives a fresh round budget. Reject closes the PR and removes the worktree.
    refused(["feedback", b], "needs text")
    code, out = fac("feedback", b, stdin="remove the FAIL file")
    assert code == 0 and job(b)["stage"] == "build" and job(b)["round"] == 3 and job(b)["round_limit"] == 4, out
    wt_b = Path(job(b)["worktree"])
    code, out = fac("reject", b, stdin="not wanted")
    assert code == 0 and job(b)["stage"] == "rejected" and not wt_b.exists(), out
    assert gh_state()["prs"][str(job(b)["pr"])]["state"] == "CLOSED"
    assert "factory" not in gh_state()["issues"]["2"]["labels"]

    # Job c: needs-info, the answer goes on the issue, then a protected-path change fails the gate, then APPROVE merges.
    ok(["step", c], "intake", c)
    write(c, "intake.md", "DECISION: NEEDS-INFO\nRISK: low\nSURFACES: none\n\n## Questions\n1. Colour?\n")
    ok(["step", c], "needs-info", c)
    assert "factory:needs-info" in gh_state()["issues"]["7"]["labels"]
    code, out = fac("feedback", c, stdin="use blue")
    assert code == 0 and job(c)["stage"] == "queued" and not (F / "jobs" / c / "intake.md").exists(), out
    assert "> use blue" in (F / "jobs" / c / "issue.md").read_text(encoding="utf-8")
    assert "Colour?" not in (F / "jobs" / c / "issue.md").read_text(encoding="utf-8")  # factory comments stay out
    ok(["step", c], "intake", c)
    write(c, "intake.md", "DECISION: ACCEPT\nRISK: low\nSURFACES: none\n")
    ok(["step", c], "spec", c)
    write(c, "spec.md", "# Spec\n")
    ok(["step", c], "build", c)
    commit(c, "factory/config.json", "{}", "weaken the checks")
    build_ready(c)
    ok(["step", c], "build", c)
    assert "M factory/config.json" in (F / "jobs" / c / "round-1" / "checks.md").read_text(encoding="utf-8")
    assert sh("git", "revert", "--no-edit", "HEAD", cwd=Path(job(c)["worktree"]))[0] == 0
    commit(c, "delta.txt", "delta\n")
    build_ready(c)
    ok(["step", c], "review", c)
    write(c, "round-2/review-code.md", "VERDICT: PASS\n")
    ok(["step", c], "approve", c)
    write(c, "decision.md", "DECISION: APPROVE\nROUND: 2\n")
    ok(["step", c], "merged", c)  # origin/main moved (job a merged), so this also tests the sync
    assert on_origin("delta.txt") and on_origin("alpha.txt") and "merge-checks" in job(c)["rounds"]["2"]

    def to_review(number, path, text):
        j = fac("create", str(number))[1].strip()
        ok(["step", j], "intake", j)
        write(j, "intake.md", "DECISION: ACCEPT\nRISK: low\nSURFACES: none\n")
        ok(["step", j], "spec", j)
        write(j, "spec.md", "# Spec\n")
        ok(["step", j], "build", j)
        commit(j, path, text)
        build_ready(j)
        ok(["step", j], "review", j)
        return j

    def to_approve(j):
        write(j, "round-1/review-code.md", "VERDICT: PASS\n")
        ok(["step", j], "approve", j)
        write(j, "decision.md", "DECISION: APPROVE\nROUND: 1\n")

    # A person merges a PR by hand during the review: `status` finishes the job.
    d = to_review(4, "hand.txt", "hand\n")
    s = gh_state()
    s["prs"][str(job(d)["pr"])]["state"] = "MERGED"
    state.write_text(json.dumps(s), encoding="utf-8")
    assert fac("status")[0] == 0 and job(d)["stage"] == "merged" and not Path(job(d)["worktree"]).exists()

    # Two jobs change the same line. The second job parks, and its worktree has no merge in progress.
    f = to_review(5, "alpha.txt", "alpha from f\n")
    g = to_review(6, "alpha.txt", "alpha from g\n")
    to_approve(f)
    to_approve(g)
    ok(["step", f], "merged", f)
    ok(["step", g], "needs-human", g)
    assert "conflicts" in job(g)["note"], job(g)["note"]
    wt_g = Path(job(g)["worktree"])
    assert sh("git", "rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=wt_g)[0] != 0
    assert sh("git", "status", "--porcelain", cwd=wt_g)[1].strip() == ""

    # The main checkout is as the user left it: same commit, same uncommitted edit.
    assert sh("git", "rev-parse", "HEAD")[1] == head_before
    assert (work / "notes.txt").read_text(encoding="utf-8") == "my uncommitted edit\n"
    assert not (work / "alpha.txt").exists()
    print("OK: all factory checks passed")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
