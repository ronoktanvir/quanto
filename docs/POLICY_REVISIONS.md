# Registered D007 policy revisions

A policy revision binds the preserved pre-acquisition plan chain, later relevance refinement, actual recorded admission refusals, acquired identities and an additive facts change. It does not admit data or calculate a portfolio. `quanto.policy_revision` makes no network or model call.

`register_revision(root, request)` accepts bounded JSON text or a dictionary. It begins a `policy_revision` submission before semantic validation. Malformed or unsupported evidence receives a retained invalid outcome; publication/storage interruption receives interrupted or pending status when the terminal record cannot be written. No retry occurs automatically. Success returns `policy_revision_sha256`, submission identity and verified artifact references.

The version-1 request contains exactly these fields:

- `schema_version`: `1`; `kind`: `policy_revision_request`.
- `predecessor_plans`: oldest-to-newest objects containing `plan_sha256` and `submission_id`.
- `refused_admissions`: ordered objects containing `submission_id` and `request_sha256`. The request artifact contains the exact submitted UTF-8 bytes, including whitespace.
- `accepted_decision_sha256` and `review_sha256s`: retained decision and review artifacts. The decision must match the SHA-256 of the approved D007_POLICY.md bytes pinned in this module’s versioned rules; installed runtime validation does not require a documentation filesystem path. The seven approved design reports (accounting, sources, integrity, operations, scope, Fable CLI and Opus CLI) are also pinned by content hash and required as a subset; additional implementation or semantic reports may be retained within the request bound. These hashes bind the archived D007 reports without authenticating their authors.
- `new_primary_facts_sha256`: the revised attributed facts artifact.
- `frozen_study`: the exact projection described below.
- `classification`: `post_acquisition_development_only`.

The frozen projection uses the existing plan field names: `instrument`, `data_start`, `data_end`, `evaluation_start`, `evaluation_end`, `lookback`, `starting_cash`, `entry_threshold`, `exit_threshold`, `cost_bps_scenarios`, `basis`, `signal_basis`, `dividend_reinvestment`, `signal_rule`, `sma_includes_current_close`, `warmup_selection`, `buy_quantity`, `sell_proceeds`, `arithmetic`, `benchmark`, `terminal_policy`, `session_order`, `dividend_rate_basis`, `split_effective_date`, and `same_session_split_and_dividend`. Costs are exactly `[0, 10, 25]`; basis is raw. Missing later mechanical detail in an early pre-acquisition ancestor is allowed, but a field already present must agree. Every projection field must exist in the latest plan.

## Evidence and ordering

Plans must have successful `pilot_plan_registration` or `pilot_plan_refinement` records whose outcome names the exact plan artifact. The first ancestor has no predecessor. Later ancestors use exactly one explicit legacy link, `previous_plan_bytes_sha256` or `previous_plan_sha256`, pointing to the immediately preceding artifact. Missing ancestors, cycles, changed bytes and tombstones refuse. Every registration's retained direct artifacts is reread.

The initial refusal is recorded `invalid/identity_change_unresolved`; the last is `invalid/unsupported_due_bill`. Additional declared intervening refusals remain ordered and are retained with their actual failure codes. Dataset, acquisitions, usage evidence and submitted acquisition requests must agree across the refusals; only primary facts may differ. Request artifacts must match submission byte counts and hashes. The existing acquisition verifier replays retained source pages and validates successful acquisition registrations without making an external request.

The post-acquisition relevance refinement must bind the initial refusal, latest refused facts, the existing structured-exclusion implementation classification and absence-of-result assertion. Its other predecessor fields remain unchanged except registration status and predecessor link. It must follow the first refusal and precede the due-bill refusal. Pre-acquisition plan registration must finish before acquisition begins. The new revision must follow the preserved refusals and plans. Ordering comes from journal sequence and matching submission-start/finish payloads, not caller-provided wall-clock strings. The complete event hash chain is checked. The change count is derived from post-acquisition plan registrations plus this financial-policy revision.

## Additive facts

The facts comparison preserves every existing top-level value, event, exclusion and source entry. Sources may be appended. Preservation compares canonical JSON values, so changing a number to a Boolean cannot evade the comparison through Python equality. Exactly one existing split event gains `regular_way_split` and sibling `semantic_review_sha256`; all its earlier fields remain byte-equivalent as JSON values. The only new top-level field is `independent_schedule_sha256`. Reordering, deleting or correcting an earlier assertion fails. The resulting JSON-path delta is retained with the revision.

This module reads the annotation-review and schedule artifacts and validates source references. Admission separately validates their financial meaning, reviewer distinction, exact annotation binding and registered semantic-review precedence. A policy revision alone cannot satisfy those admission checks.

`validate_revision(store, digest, admission_request=None, before_submission_id=None)` rederives the entire revision, verifies successful registration and request bytes, and compares its policy and caller-provided loaded-code identity with current code. When supplied, the admission request must equal the latest refused request with only revised facts and `policy_revision_sha256` added. The revision must finish before the supplied admission submission begins. The returned object includes `policy_revision_sha256`, `artifact_refs`, `frozen_study`, `lineage`, and `facts_delta`.

`validate_study(store, revision, study_request)` checks dataset, dates, strategy parameters and one allowed cost. A digest argument causes revision revalidation; a dictionary argument is for callers that have already validated the revision. Separate suite registration proves membership in the complete three-scenario roster. The caller includes this module in disk and loaded-code identity and revalidates before and after calculation.

## Trust and limits

Registration records attributed judgments under cooperating application controls. Hashes and ordering are not authenticated reviewer identities or proof of independent thought. SQLite and local objects are not immutable against their owner. The event chain detects ordinary corruption and inconsistent ordering; complete owner rewrites or deletion of an uncheckpointed suffix are outside this threat model. Source truth, acquisition rights, market completeness and operational settlement behavior remain separately qualified. All acquired data remains development-exposed; this revision cannot restore a holdout.
