# D008 role-output contract clarification

**Recommendation: make the existing role-to-decision map and predicate-preservation rules explicit in fixed system-prompt text, without changing the parser or packet schema.** This is a routine clarification within accepted D008 if it preserves every existing choice and all financial, privacy and spending boundaries. It is not evidence that ambiguous wording caused the actual scope failure, and it does not authorize another paid attempt.

Reviewer: `/root/d008_broker_critic`. Public-source checkpoint: `e02d9cd1e4792fad3a124a31725d97aaa0f00d41`. This assessment read only public product/test/governing source. It did not inspect runtime, provider responses, rationale, private data or environment files, execute tests, call a model/network service or modify product source. The only new output is this report. Product source remains frozen until the current actual numerical and scope audits finish.

## Observed contract and interpretive limit

`research_packets._DECISIONS` already assigns exact choices to all seven roles. `_output` enforces that map, requires a null director predicate, requires a supported predicate for a hypothesis proposal, and requires engineer and all four review roles to preserve the selected hypothesis predicate. `parse_role_output` additionally binds the output role and contextual aliases. `research_dispatch` derives the required predicate from the actual hypothesis proposal in `prior_outputs`; it does not choose a replacement.

The current prompt names director, hypothesis and engineer individually, then says “Review decisions are no_blocking_method_issue, block or inconclusive” and “Engineer and reviewers must use the predicate selected by the hypothesis prior output.” Those sentences do not explicitly enumerate `data_critic`, `statistical_critic`, `quality` and `scope`. The prompt also uses generic “stop or block” language elsewhere, although `stop` is not a valid decision for those four review roles. The parser is precise; the prose relies on the model to classify roles and interpret generic language in context.

The reported actual scope response had disallowed decision and predicate fields. That observation establishes a response-contract violation, not its cause. The absence of explicit role names is a plausible ambiguity to remove, but the model could still violate an unambiguous contract. No raw rationale was read for this assessment, and no controlled comparison isolates the prompt wording.

## Smallest reviewable correction

Keep one fixed system prompt for all roles. Replace the generic decision sentences with an explicit role-to-decision block, deterministically rendered from the existing `_DECISIONS` constants in `ROLES` order with sorted enum values. It contains program constants only, never raw model prose, private IDs or new evidence. This avoids maintaining a second independent decision map. It also avoids the broader contract changes required by a different dynamic system prompt for each assignment: the current broker freezes one `SYSTEM_PROMPT` hash, and dispatch verifies that same hash.

The block must express exactly this existing map:

| Role | Permitted decision codes |
| --- | --- |
| `director` | `proceed`, `stop` |
| `hypothesis` | `propose`, `stop` |
| `engineer` | `execute`, `stop` |
| `data_critic` | `no_blocking_method_issue`, `block`, `inconclusive` |
| `statistical_critic` | `no_blocking_method_issue`, `block`, `inconclusive` |
| `quality` | `no_blocking_method_issue`, `block`, `inconclusive` |
| `scope` | `no_blocking_method_issue`, `block`, `inconclusive` |

Adjacent fixed text should state the following exact semantics:

- `role` must equal the input context's role. `decision` must be one of that exact role's listed codes; these are not interchangeable labels or suggestions.
- Director's predicate is null. Hypothesis `propose` requires one code from `allowed_predicates`; hypothesis `stop` may retain an allowed code or use null, matching the existing parser.
- `engineer`, `data_critic`, `statistical_critic`, `quality` and `scope` must return the exact predicate code selected by the hypothesis proposal in `prior_outputs`. This applies to every permitted decision, including engineer `stop` and reviewer `block` or `inconclusive`.
- The predicate field names the test being discussed. Preserving it does not mean the predicate is true, the model endorses execution, or the review is favorable. Do not replace it with a truth value, conclusion, null, synonym or another predicate.
- Every permitted decision remains available. Do not prefer agreement or `no_blocking_method_issue` because prior stages completed, a suite passed integrity checks or a failure appears in a reviewed historical lineage.

Qualify the existing generic “stop or block” sentences with “using the permitted decision for your role,” and explicitly retain `inconclusive` for the four named review roles. Do not add a new reviewer `stop` decision to make the prose true. Do not remove or narrow `block`, `inconclusive` or any existing stop path.

No populated example response or default decision is needed. In particular, an example that preselects `no_blocking_method_issue` or one predicate would add avoidable pressure. The all-role block plus the exact field rule is sufficient; a new outbound response-contract field, per-role prompt API, retry prompt or parser repair layer is unnecessary for this correction.

## Required validation before integration

These are recommended checks, not executed results from this assessment. Reuse existing tests where they already cover the behavior; add only missing coverage.

1. **Prompt/parser agreement.** Verify the rendered decision block covers exactly seven role keys and exactly each existing enum, including all three decisions for `quality` and `scope`. Confirm deterministic rendering and one fixed prompt identity across roles. The prompt must explicitly name the five roles subject to predicate preservation and explain that a negative or inconclusive decision does not change the predicate.
2. **Decision freedom and predicate identity.** Exercise every allowed decision with valid role context. Engineer `stop` and each review role's `block`/`inconclusive` must retain the exact selected predicate and remain valid. A different otherwise-supported predicate and null must still refuse for all five dependent roles. Preserve both permitted hypothesis-stop predicate forms and director-null behavior. Existing `test_verified_integrity_preserves_free_stop_block_or_inconclusive_decisions` and `test_engineer_and_critics_require_exact_selected_predicate` provide much of this coverage.
3. **Strict rejection and partial history.** Use an invented last-role response with a wrong decision and predicate, without copying actual private response tokens. Confirm the unchanged parser refuses it, its private response remains retained, the hold/effect remain uncertain, six stages remain published, review outcome stays `incomplete`, and there is no repair, extra dispatch, release or automatic retry. Preserve an inconclusive data-critic output in a separate successful-parser fixture; completion must not turn it into clearance.
4. **Identity, privacy and bounds.** Confirm the new prompt hash reaches frozen role contracts, the prepared body and failure-context implementation identities. Old proof/context identities must not silently pass as new ones. Recompute synthetic worst permitted packet/request byte sizes and conservative reservations for both configured models under existing limits; do not raise limits to accommodate the text. Re-run existing private-egress checks on complete rendered packets. JSON schemas, aliases, predicate vocabulary, numerical/source omissions and all financial-module identities remain unchanged.

A prompt-only source change should normally be limited to `research_packets.py` and its targeted tests, with existing broker/dispatch integration tests reused or narrowly extended for the partial-failure invariant. Prompt/source hashes necessarily change; the existing packet/schema fields need not change when their meanings and parser remain identical. Freeze exact new bytes and obtain separate critic, quality and scope dispositions before integration or any proposed actual use.

## Decision classification and limits

This is **routine D008 implementation** because it communicates already enforced constants more explicitly. It adds no role capability, new objective, permitted decision, predicate, market assumption, data access, egress field, financial calculation or spending authority. It preserves researcher choice, independent objections and conservative failure handling. Under the contributor instructions, routine implementation within an accepted decision does not require another five-perspective policy council merely to restate the parser accurately.

The classification would change if the correction broadened or reinterpreted decisions, defaulted/changed the hypothesis selection, automatically converted an invalid reply, forced a favorable conclusion, exposed more evidence, changed financial rules or authorized automatic retries or increased spending. Those would require the applicable new decision review; this report does not approve them.

Keep all three actual attempts, their rejected outputs, spending states and review findings unchanged. Finish the pending actual numerical/scope audits against frozen source first. A clearer prompt may reduce avoidable format violations, but that is an untested prediction. Neither this recommendation nor a passing synthetic fixture establishes a successful future actual workflow or authorizes another paid attempt.

## Inspected identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_packets.py` | `ead052fb0fe53576eff02a5f7138af16a58b70c0c5fbd164eb196f4af92e0a93` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_broker.py` | `aa4f9e93f9fc471273bf2e6c1a0d67acb74583228618cecd17aa9ec513419e34` |
| `src/quanto/research_failure_context.py` | `b99af35355b14d638770c069791124a8d72774346e5a9677ac74d607bc777208` |
| `tests/test_research_packets.py` | `b156abdedbc5df734856dcabcb02ff4a17d3e0925c09de3ba6d2ffd06767430a` |
| `docs/D008_POLICY.md` | `91bd473d6972355c8cba447fff7b1e66e9b77bddf9712097ebd0f95bafc07aa7` |
