# D008 broker implementation criticism

Review status: both P1 transport findings and the P2 parent-effect lineage finding are closed after independent rechecks. No blocking finding remains within the stated bounded scope. The reviewed scope is one explicit bounded development workflow. Synthetic execution does not certify actual operational models, historical acceptance, autonomous research scheduling, protected evaluation, paper operation or live execution.

Reviewer: `/root/d008_broker_critic`, separate from producers and from the independent quality/scope roles. Base revision: `fc1c8c4e3c5f8dd37c77617f6a121d2ed42f57af`, with the uncommitted implementation identified below. I read the governing project records, D008 policy, broker contract review, implementation and related tests. I accessed no project runtime, private source data, environment file, credentials or external service. All executed reproducers used temporary invented fixtures and injected model responses; no actual model request or financial acquisition occurred. This report is criticism, not the separate quality or scope certification.

## Findings and dispositions

### P1: stale final guard could send after lease expiry

The original `ResearchDispatcher._before_send` cached `now` before verifying local artifacts and readiness. Those operations could consume the remaining lease while the guard still returned a positive timeout calculated from its earlier timestamp. Post-response publication then refused, but it could not undo the already emitted request.

Independent minimal reproduction used `test_research_dispatch.setup` with its 60-second lease. Inside the final guard only, I wrapped `_verify_refs` to run its original checks and advance the synthetic clock by 61 seconds. The injected transport was called at `2026-11-02T00:01:01+00:00`; the request subsequently became uncertain. Thus the defect concerned actual send authority, not merely output publication.

The producer now refreshes the clock after local verification/readiness reads, rechecks the live lease and accounting day, and calculates the timeout from the refreshed time. Rerunning the original reproduction produced zero transport calls and retained the uncertain hold. **Closed by independent recheck.** Producer regression coverage additionally exercises both slow verification and slow readiness across lease and Los Angeles day boundaries; I independently ran that coverage.

### P1: authorization could charge the research allowance to the wrong day

The original `_authorize` calculated research-purpose usage and its day before `_start_intent_locked` verified local references. The unchanged journal reservation/dispatch functions obtained fresh timestamps. Crossing Los Angeles midnight during that local work therefore allowed a current-day global reservation with a previous-day purpose allocation, bypassing the current day's USD4 research allowance.

Independent reproduction set the clock to `2026-11-02T07:59:50Z`, prefilled November 2 research usage with 4,000,000 microUSD, and advanced 11 seconds immediately after the original `_start_intent_locked`. The request completed. Its global reservation belonged to November 2 while its 73,244-microUSD research allocation belonged to November 1.

The repaired authorization refuses a day crossing after effect-start verification, checks purpose usage using that consistent day, and revalidates lease plus reservation/dispatch day consistency before atomic commit. The identical reproduction now raises `Research authorization crossed Los Angeles midnight`; no new reservation, purpose allocation, effect start or dispatch survives. **Closed by independent recheck.** The preexisting next-day allocation remains intact.

### P2: interrupted comparison requires an exact parent-effect link

The lead identified a separate audit gap: before the proposed repair, the private comparison receipt was attached to the broker stage only after the comparison returned and the handoff completed. Two concurrent workflows can produce identical safe role projections and therefore identical comparison request identities. A crash after launch could retain both calculations without uniquely identifying the parent assignment, fence and consumed launch intent for each child. The no-retry behavior limits repeated effects, but does not establish exact causal lineage.

I assessed this as a required P2 correction for the bounded workflow's audit contract. The implemented additive repair precommits the exact private tool request, parent submission, assignment, intent and fence. A callback binds the unique child submission immediately after its creation and before validation or suite execution. It verifies the live capability, consumed effect, child kind/state and exact request bytes; uniqueness constraints prevent child or effect reuse. Callback failure aborts computation.

I independently injected a process interruption immediately after the real local comparison returned successfully but before the broker received its receipt or published the engineer handoff. The parent remained pending while the exact parent/assignment/intent/fence-to-child link survived; the child comparison, its fresh suite and all three suite children were successful and the event chain verified. A same-key repeat refused before transport. **Closed by independent recheck.** The producer tests also cover interruption just after binding, callback refusal before financial work and duplicate child binding; I ran them independently.

An initial fault-injection attempt patched the legacy suite entrypoint directly and was refused by code-identity validation before workflow creation. No financial work ran in that attempt. I moved the interruption to the additive broker boundary to exercise the intended crash window without changing the historical engine identity.

## Executed evidence and limits

After both transport repairs, I independently ran `tests/test_research_broker.py`, `tests/test_research_dispatch.py`, `tests/test_research_packets.py` and `tests/test_research_comparison.py`: **206 passed in 49.29 seconds**. These include complete seven-stage composition on invented data, actual local admission/suite/calculation entrypoints, concurrent global budget refusal, retained research-purpose holds, stale/cancelled capabilities, private-response separation, malformed outputs, no automatic replay, changed-code refusal, exact fresh-invocation ancestry, old-result substitution, Decimal comparison counterexamples and separate candidate/attempt accounting. They establish software behavior on `synthetic_fixture` evidence, not investment performance or real-model competence.

After the lineage repair, I independently reran the complete broker and comparison suites: **67 passed in 52.50 seconds**. This later run covers the final changed broker/comparison artifacts; the transport and packet files remained unchanged from the 206-pass run.

An earlier run during concurrent source edits reported 199 passes and one broker integration failure. The affected test independently reran successfully, followed by the complete 206-pass run. The initial failure remains disclosed; it is not included as successful verification. A failed attempt to use the host `shasum` utility also encountered a locale configuration error; final hashes use Python's SHA-256 implementation.

The strict packet vocabulary excludes private prices, dates, provider identifiers, arbitrary raw errors, raw rationale and predicate truth. Later models receive lifecycle categories and bounded safe projections. Local alias bindings identify the retained artifacts; they do not establish that a model inspected hidden numerical data. Both numerical predicate outcomes project to the same completion category. Direct comparison functions remain trusted local APIs, and only the broker's actual trace can establish real role authorship.

Broker code identity currently records source bytes and Python identity, whereas the derivative also records loaded-function identities. This is a qualification for future persistent-process operation: a source update and an already loaded process need explicit revision coherence. The present entrypoint is a one-shot CLI and checks source identities between stages and at completion; this review does not certify a hot-reloaded or long-lived supervisor. Application capabilities and the ledger constrain cooperating processes, not a privileged owner or unrelated account clients.

I verified that `ledger.py`, `provenance.py`, `research.py`, `event_engine.py`, `admission.py`, `explorer.py`, `policy_revision.py` and `study_suite.py` remain byte-identical to the base revision. No financial-policy or historical-admission identity was relaxed.

The later actual five-role acceptance still requires available budget, observed actual model evidence, a materially selected new historical development calculation, distinct criticism, executed independent quality, separate scope findings and independent review of the exact trace. The implementation's `operational_acceptance=False` remains necessary. R14 and the complete operation remain incomplete.

## Final inspected artifact identities

| Artifact | SHA-256 |
| --- | --- |
| `src/quanto/research_broker.py` | `ad8fe8f46103c85fdf77dd4ade94449f504d449ed5e01d580934312d6b8bd6b4` |
| `src/quanto/research_dispatch.py` | `120834deb63abebeeb54a14f8cf470ad43fd9ac1f44979ee96fe9c88ba20c1f1` |
| `src/quanto/research_packets.py` | `81232c126b7a50b54dad92f7339ce41de80899d709358c9a4ae8a6efe23dcdeb` |
| `src/quanto/research_comparison.py` | `c2e933841f1664b62528b4342b37a34e7b3452e7783d91f495f78a6b05d65446` |
| `src/quanto/provider.py` | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |
| `src/quanto/research_workflow.py` | `64ca63f155a2417021bb8632673f14ec12ff7d497881aa13a95d7330911ab02b` |
| `src/quanto/cli.py` | `7201b943efea1777c70e0fff7ce3d2e953089ba58648e360e53b5f6a22dabbd7` |
| `tests/test_research_broker.py` | `25c6b971df6ca9286ef196a1d76a30cca2a4f056a8e246c2e767c12882c07129` |
| `tests/test_research_dispatch.py` | `fac65cd292e8c7a13c0c62f514a17a17963787bb26838eab348f6e6d7e9eb616` |
| `tests/test_research_packets.py` | `dd35ec89718b3b0b5678443eba58ca9a25f9d5153c1c6171f6de34ac0a307897` |
| `tests/test_research_comparison.py` | `95e920e547e9a56daf9adab032eba0d5d1b0b946d182364f78d9546636ede88a` |
| `tests/test_provider.py` | `87083d561434fdb7eae9c100bc027400397cfe3cbd000b3336d7c2fac347fe59` |
