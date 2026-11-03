# D008 development rollout: source-only criticism

The proposed legacy-unknown bootstrap can be implemented within accepted D008 without reading research data, issuing access effects or making provider/model calls. Its separation from website reload and protected eligibility is correct. **Actual execution is not cleared:** the concrete controller must distinguish its own successful creation from a concurrent creator's store, verify the complete bootstrap footprint, and demonstrate bounded termination across both child processes before use.

Reviewer: `/root/access_v2_critic`, distinct from the planner and lead executor. I inspected plan `a109a5effa8c5cd5916443cfce30a8ab9c25a509b2f5b35359f2358c9ea5389a`, accepted D008 and the public source at `6f844e40761ff1b75d4a83251b4a15b9c0575761`. No actual runtime/configuration, credential, private database, process state or recovery candidate was inspected. No constructor, controller, service, provider/model request, synthetic product test or actual bootstrap was executed. Only this report is written. The findings below are source-level requirements for the subsequent controller, not observations of the owner's current processes or files.

## Why the narrow operation is feasible

The pinned registry imports standard-library code and creates its control store independently of `Provenance`, `Journal`, conversations and acquisition workers. Its initial legacy decision uses existence checks on the research database, object directory and artifacts path; those checks do not require opening their contents. With the expected existing-development condition, creation records `legacy_unknown=True`. No supported operation clears that marker. Session opening validates the existing principal and root/control identity; closing permanently disables that session. A fresh child can reopen the same persisted authority without an access intent or provider call.

The plan properly excludes reservations and `protected_acquire` from an actual smoke test. Even a refused protected call would add an audit event, and a real reservation would be a different operation. Protected flags can remain false on the inspected source/verified configuration contract without attempting either. No current numerical data needs to serve as a positive test fixture.

The constructor's existing-file path also supports the proposed failure discipline: an empty/partial or differently bound file is not silently initialized. However, creating schema/triggers precedes the configuration transaction. A failure during that sequence can therefore leave a persistent partial file, which later constructors correctly refuse. Such a file must remain part of the failed attempt's evidence, with separate reviewed reconciliation rather than deletion and replay.

## Required controller precision

### R1 — prove that this attempt won exclusive creation

The plan's preflight absence check is necessary but insufficient to attribute the new store to this attempt. `Supervisor.__init__` tries an exclusive `os.open`; on `FileExistsError`, it takes the existing-store validation path. Another cooperating process could create and commit a valid store between preflight and that call. The subsequent constructor can then succeed, with matching root/schema and one bootstrap, even though this attempt did not create it. A preflight stat, creation-window timestamp or matching final counts cannot distinguish those histories.

The concrete controller must retain trustworthy in-process evidence that its bootstrap child actually succeeded in the exclusive-create branch and bind that result to the created file identity and private intent. It must refuse unexpected adoption of a concurrently created file. The planned fresh-child reopen is a separate, intentionally allowed operation against the first child's exact identity; it must never create a replacement if the file disappeared. Do not precreate an empty control file as a lock: the reviewed constructor would correctly treat that as an invalid existing store. Use an independently reviewed observation mechanism or an explicit reviewed API if needed, without changing creation semantics or claiming protection from a hostile filesystem owner.

Add synthetic races/interleavings for a creator appearing after preflight, a file disappearing before reopen, and an existing valid store at first entry. Only the intended creator/reopener histories can pass. An unresolved creation owner remains unaccepted even if its configuration looks plausible.

### R2 — verify the whole expected bootstrap state

Checking only zero intents/effects/reservations/publications does not establish that no other administrative operation occurred. The registry also has principals, relations, revocations, classifications, producer capabilities, page permits, widening records, terminal tables and audit records. `overview()` is deliberately narrower than a complete bootstrap verifier.

The controller should verify the exact expected configuration keys and values, one expected default principal, exactly one valid bootstrap audit record with the correct legacy/synthetic values, and empty remaining application tables. Check the supported schema and append-only triggers from the pinned source, rather than interpreting the configuration string `schema=2` as a complete schema validation. Bind a canonical bounded state identity after creation and require the same logical state, principal/store identity and physical control-file identity after fresh-child session open/close. This remains local consistency evidence, not an external freshness or antirollback claim.

Private values stay in the operation's private receipts. Public evidence can state fixed agreement/limitation flags and table counts, without root paths, principal/store identifiers or arbitrary control payloads. The helper must not read research contents to construct this witness. SQLite's control-file journal sidecars and newly created control directory are part of the permitted control-store write footprint; they are not permission to write research.sqlite or operations history.

### R3 — give the whole operation one bounded lifetime

The proposed 30-second work and 40-second outer bounds should cover the entire creation/reopen sequence, not restart separately for each child. Bind both exact interpreter invocations and imported/compiled source identities. Pin bytes before loading them, refuse mismatch and exclude inherited credentials and startup paths that can load unreviewed project code. A disk hash measured beside unrelated already loaded objects is not adequate execution identity.

The outer controller must own, observe and terminate its actual child handles, including a child still running when the controller times out. No orphan reopen or bootstrap may continue after the operation is considered terminal. Rehearse interruptions before creation, during schema/configuration setup, after the first commit and during reopen/receipt publication. Keep the durable outer intent and every partial outcome; a missing result never authorizes an automatic second create. Clean outer termination plus the bound private receipts is required for adoption. This does not authorize killing unrelated Python processes or clearing restart circuits.

## Process cut and website boundary

The plan correctly requires an actual entrypoint/process inventory before execution, while this review supplies none. Root must establish that identified research/acquisition workers are terminal or quiescent through authoritative ownership/liveness evidence and prevent new work from being admitted during the cut. An archived assignment, old PID, idle-looking status file or absence of recent output is not that evidence. If the cut cannot be established, stop before first creation and preserve the reason.

Website supervision is a separate concern. The inspected operations service can preserve a healthy external server, writes its state even with `--once`, and can request paid incident diagnosis in normal operation. Readiness checks validate status/assets, not the server's loaded module identities. The dashboard's conversation backend is lazy, but its session/conversation routes can initialize databases and use direct journal/provider paths. Therefore the bootstrap result may describe zero effects and calls **by the bootstrap operation**, not certify global inactivity or updated enforcement across a concurrently running website.

No service restart, model-pause change, diagnosis, `.env` access or conversation initialization belongs in this controller. A later service operation needs its own exact ownership, in-flight-call, pause-state and loaded-identity checks, as the plan already states. Healthy unknown port owners remain untouched. Preserved research bytes, an initialized registry and a healthy webpage are three different facts; none substitutes for the complete application rollout.

## Disposition and inspected identities

The plan is suitable for preparing a controller with R1–R3 incorporated and independently rehearsed. There is no new financial, statistical, disclosure or isolation decision requiring another council for this bounded bootstrap. A stronger process-isolation claim, automatic history reconciliation, weaker recovery gate or protected activation would require a different reviewed decision. This review grants no actual execution outcome and does not ask for a repeated owner approval.

| Public source at the inspected commit | SHA-256 |
| --- | --- |
| Registry | `c69c7de7e66c0d6f8b372304db482bf6d83ad0fe35960e55fc8fa00ac4a4b113` |
| CLI | `69b4301ab74530659d5433967512bbf3cbaf423f9c96d8f6e1fd2c91a4c6f02d` |
| Provenance | `c765ffdfbbaeed019b82552a2ad97b1ebf14699960582600ca372996e661f5f9` |
| Operations | `65004d79a24fffb83b6d2485b34bd3b181aa425c41de501760bf0560264c24bc` |
| Dashboard | `f22b030d640d56d34a24774cafcd4d70f72c19cf1c403b2cb52c2616b27003b8` |
| Conversations | `a704d127f14df9dc6d6757f6182c899e875d58ea46292666b53efeb2ec46a8a3` |
| Provider | `5f4f214d079bd4a17ddc3049163d5a3bfc9acd8ba2508a3dfe2f5ad5c4c0ace0` |

Protected eligibility, legacy reconciliation, complete route/process rollout, evaluator isolation/release, multi-store recovery, sustained research roles and paper/live readiness remain incomplete. The older D009 research generation cannot acquire this later control history merely by being restored.
