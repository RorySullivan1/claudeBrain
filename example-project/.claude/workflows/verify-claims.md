# verify-claims

Take an asset that asserts facts about an external system and establish, claim by claim,
whether those facts are true — then label each one with its provenance so a future reader
can tell a vendor-documented rule from somebody's Tuesday afternoon.

Run this **before shipping** a skill or context doc that carries factual weight, and when
adopting an asset from elsewhere. It is the truth gate; `skill-creator`'s evals are the
performance gate. They are independent — an asset can pass evals while asserting something
false, and that is the failure this workflow exists to catch.

**Inputs:** a target asset (a `SKILL.md`, a context brief, a bundle).
**Output:** the asset updated with tier-labeled claims and dated citations; a report of
what was verified, what was corrected, and **what could not be verified**.

## Steps

1. **Extract the claims.** Read the asset and list every falsifiable factual assertion
   about an external system — API signatures, property/constant names, platform limits,
   default values, behavioral quirks. Skip judgment, style, and preference; those are not
   claims and must not be dressed as such.

2. **Triage by what would settle each one.** Apply the `claim-grounding` triage table:
   authority-settled (a live system can answer), doc-settled (vendor documentation
   governs), experience-settled (only observed behavior supports it), or not-a-claim.
   Sort by blast radius — verify what a reader will *act on* first.

3. **Ground the doc-settled claims.** Query the governing source and confirm the sentence
   actually says what the asset says. For Microsoft surfaces use
   `mcp__Microsoft_Learn__microsoft_docs_search` then `microsoft_docs_fetch` for the full
   page; otherwise `WebFetch` the spec. Record the URL **and the retrieval date**. A
   citation that doesn't contain the claim is a failed check, not a passed one.

4. **Ground the authority-settled claims** *(only where a probe is available)*. Build the
   smallest probe, run the known accept/reject controls first, round-trip the input, and
   promote only confirmed outcomes. A timeout or harness failure is a **non-result** —
   stop the line, don't record it as a negative. Keep the probe local; never wire it into
   CI or a shipped command.

5. **Label the rest honestly.** Any claim that survives without a doc or a probe gets
   marked experience-settled in the asset itself, naming where it was observed. Do not
   delete it and do not launder it — an accurate weak label is more useful than either.

6. **Correct what's wrong.** Fix false claims at the source; delete claims that turned out
   to be unfounded and unverifiable. Never soften the check to make a claim survive.

7. **Record the judgments** for anything that took real work to settle, per
   `references/ledger-schema.md` — identity, verdict, rationale, `grounded_by`, and date.
   This is what stops the same claim being re-argued next quarter.

8. **Report.** State what was verified and how, what changed, and — the part people drop —
   **the claims still unverified**. An honest gap is a finding; an unmentioned gap reads as
   coverage that was never there.

## Control flow / stop conditions

- **No falsifiable claims** in the asset → **stop**, nothing to do here. A skill that only
  teaches judgment needs no grounding pass.
- **Sources disagree** (docs vs observed behavior, or two vendor pages) → **stop and report
  the drift.** Do not pick whichever source makes the claim convenient; surface the
  conflict and let a human settle it.
- **A probe's controls fail** → **stop.** The harness is broken; nothing it produced this
  run is evidence.
- **All claims tiered, labeled, and dated** → **done.** Hand off to `ship-version`.

## Invokes

- Skill: `../skills/claim-grounding/` (the triage, grounding, and ledger discipline).
- Reference: `../skills/claim-grounding/references/ledger-schema.md` (record shape).
- Tools: `mcp__Microsoft_Learn__microsoft_docs_search` / `microsoft_docs_fetch`, `WebFetch`.
- Hook: `../hooks/asset_integrity.py` (structural check — complements this semantic one).
- Workflow: `ship-version.md` (ships once the truth gate passes).
