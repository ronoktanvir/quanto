# Materialized generation: actual finite-inspection refusal

The new read-only inspection passed its initial snapshot verification, then refused while collecting graph roots. No graph or terminal success result was produced. The original materialization remains accepted only as a local exact-byte copy; complete dependency coverage remains unverified.

The lead reviewed controller `c6ea3809d99247b45926add01666918136e6414a9a158c73166daa12315c29e9` as recorded in the separate controller review, then invoked it once from an isolated Python child with minimal PATH/LANG/LC_ALL environment, disabled stdin, exclusive private logs and a 70-second outer timeout. Its 45-second closure and 15-second base-verifier bounds were unchanged. The launch began at `2026-11-03T02:23:58.686837+00:00` and ended at `02:23:58.872976+00:00`: 0.185914 seconds, exit 1, zero stderr and no timeout. The controller recorded 0.104635 seconds after its durable inspection intent.

The fixed refusal code was `malformed_supported_profile`. Bounded traceback observation found the exact frozen inspector's `graph_root_registry` call site; no recovery, OS or SQLite error code was reported. This establishes the stage for this attempt, not the specific malformed predicate, corrupt data or the original failed attempt's cause. The initial verifier precedes that call in the frozen implementation. Final verification was not reached. No counts or partial in-memory graph are adopted.

The lead checked owned private stable receipt files, controller identity, stdout/failure equality, process/intent bindings, every original input pin and absence of graph/result/pending receipts. The safe projection reports those lead checks; reviewers do not independently inspect the private candidate or original receipts. The attempt and launcher are consumed and must not be rerun.

| Evidence | SHA-256 |
| --- | --- |
| Safe actual projection | `1f845615968ac9fdb79f2e42141f48a60ae78b5148166f5b65ad66ca0225210d` |
| Launcher intent | `27a1aee550bf822ea2b3a1f9834c3f77b1dfb569696fe615b77ed073e1899b4c` |
| Inspection intent | `4a1260515ff8a0f08b09146bf9698dc13e5277eb6e69d89393f61e08726a09b9` |
| Failure receipt | `8f6c37fa917e300cebe866fe33d3a6a715963a77c9f84796689bc758b7c83205` |
| Launcher process outcome | `f44aa9a379ed02c6aeefe5af2b976aff3bc89d412926cb996c51268240af44c1` |

The next diagnostic must isolate the root-shape mismatch using bounded read-only checks, reviewed independently before actual use. A successful local copy does not authorize weakening known-profile validation. Any implementation correction needs reproduced evidence, targeted regression coverage and separate criticism/quality/scope disposition. Unknown coverage remains explicit.

No new production capture or materialization, provider/model call, financial replay, upload, authority restore or trade occurred. All full/typed/off-Mac/offline/replay/execution flags remain false. Earlier capture, failed closure and two diagnostic refusals remain preserved. The future D008 control database is absent from this old research generation. Required source/audit closure, source-use permission, external key/account recovery, encrypted transfer, downloaded restore and trusted freshness/effect barriers remain incomplete.
