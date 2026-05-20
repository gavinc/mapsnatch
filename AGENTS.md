# AGENTS.md

> If `SOUL.md` exists in this repo, read it before proceeding. It defines
> personality and values. If absent, operate with professional restraint.

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
