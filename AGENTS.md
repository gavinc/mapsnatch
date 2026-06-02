# AGENTS.md

> If `SOUL.md` exists in this repo, read it before proceeding. It defines
> personality and values. If absent, operate with professional restraint.

---

## Issues-first workflow (mandatory)

**No ticket, no workee.** Do not implement features or bugfixes requested in chat until a tracking GitHub Issue exists.

| Request in chat | Agent action |
|-----------------|--------------|
| New feature | Create issue (`[feat]: …`) via `gh-ll issue create`, then branch |
| Bug / regression | Create issue (`[bug]: …`), then branch |
| Question / explanation only | Answer; no issue required |
| Docs typo (one line) | Fix directly; issue optional |

Before writing implementation code:

1. Confirm repo has a GitHub remote and `gh-ll` auth for the `gavinc` identity (**github-identity-management**).
2. Open or find the issue; note the number.
3. Branch name should include the issue number when practical (`feat/123-short-name`).
4. PR body must include `Fixes #N`.

**Exceptions** (no issue required):

- Operator explicitly says "skip issue" or "no ticket".
- One-line typos, comment-only edits, or doc fixes with no behavior change.
- Active production incident when the operator declares hotfix mode.

If the operator describes substantive work but no issue exists, **create the issue first**, paste the URL back, then proceed.

---

## Progress Reporting

Each update is one line:

```
<STATE> | <DELTA> | <NEXT> | <ASK>
```

**STATE:** `moving` · `blocked` · `done`
**DELTA:** What changed. New only. No history.
**NEXT:** What happens next without operator input.
**ASK:** Required operator action, or `none`.

Rules:
- One line. No logs, no reasoning.
- `moving` → ASK is `none`
- `blocked` → ASK is concrete and actionable
- No meaningful change twice in a row → STATE becomes `blocked`

```
moving | tests added | running CI | none
blocked | missing env var | waiting | add STRIPE_KEY
done | deployed to prod | monitoring | none
```

---

## Decision Contract

**Ambiguity** — Ask before acting. One focused question, not a list.
**Done** — Tests pass. Code committed. Operator unblocked.
**Scope** — Do exactly what was asked. Flag additions as options; don't implement them.
**Blockers** — Surface immediately. Never work around a blocker silently.

---

## Communication

No narration. No recaps. No "here's what I did."
Report results, not activity. If nothing changed, say so.

---

## CursorVox cockpit (visual review)

For **CursorVox** UI judgments ("go look at the interface"), use the mobile screenshot harness and vision on the PNGs. See **`~/coding/cursorvox/AGENTS.md`** (Visual review section): `cd ~/coding/cursorvox/frontend && npm run capture-ui`, then read `screenshots/mobile-cockpit/*.png`.
