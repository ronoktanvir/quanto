# D008 manual cycle supervisor quality

**Actual-use clearance is withheld for joint freeze v1.** All 59 frozen tests passed. Two additional integrations using the real registration helper, product validators and worker reached the expected refusal boundaries. The separate implementation critic also reproduced ownership, expiry and receipt failures on this freeze. The successful predispatch paths have a narrower scope than those findings. A corrected supervisor and the separately outstanding auditor correction need independent recheck before an actual cycle.

## What ran

I used the approved v2 registration fixture to create two distinct marked, credential-free projects outside the real workspace. Each began with its own invented request history and development authority. The unchanged registration controller ran the real policy-revision, admission and suite registrations in three isolated child processes. Each child exited zero, produced a fresh mapped submission and was absent at the subsequent PID check. Both registration parent calls exited zero.

In each case, the frozen supervisor's `build_request` constructed the request from the invented template and the newly registered suite. A fresh isolated Python 3.11.9 worker received an invented, bound context through `run(context_factory)`, which invoked the unchanged `paid_worker.execute()`. The registration, `Supervisor`, `Provenance`, broker configuration, suite verification, provider readiness and credential lookup code used their ordinary implementations. I observed function entry, return and refusal without replacing a product method or supplying a model response. Independent guards denied network, credential-file reads, unrelated workspace data and any attempted broker dispatch. Both environments were empty when requested, both invented roots lacked `.env`, and no guard veto fired.

| Separate invented root | Last observed boundary | Terminal evidence |
| --- | --- | --- |
| Existing `runtime/model_calls_paused` | Broker configuration parsed and suite verification returned. `provider._research_ready` raised `Model calls are paused` before credential lookup. | Worker exited 1 in 2.00 seconds. Parent reaped it and confirmed its PID absent. |
| Pause absent, key genuinely missing | Suite verification returned, provider readiness returned, and `local_key` returned `None` for the invented project. The worker refused before its spending observation. | Worker exited 1 in 2.03 seconds. Parent reaped it and confirmed its PID absent. |

Both workers consumed the attempt before checking the suite. Each retained before/after state, an uncertain outcome and a matching `refused_or_uncertain` terminal receipt. Neither emitted `prelaunch-budget.json`, `prelaunch.json` or `paid-call-entered.json`. No `run_workflow`, financial replay, model response, network request or paid call occurred. The worker's conservative generic outcome preserved uncertainty even though this independent observer established where these two invented processes stopped.

**The refusals changed control history.** In each store I compared every application-table row before and after worker invocation. All previous control rows remained exact prefixes. The only additional rows were 60 `content_read` intents, 60 effects, 60 effect completions and 180 audit rows. All research tables retained their exact rows. The worker's uncertainty-marked after-state agreed with the initial source, compiled and loaded identities. These counts belong to the invented suites. They are evidence that local suite checks have durable access effects even before model dispatch.

## Evidence boundaries and preserved attempts

The 59 supplied tests passed in 4.11 seconds. They comprise five supervisor cases, including real operating-system children with invented stage implementations, and 54 worker cases, including budget-snapshot and environment checks. The new integrations directly connected real registration results to the real worker on two refusal paths. They supplied invented parent receipts and the internal context on purpose. Actual bootstrap, parent review authorization, a successful paid dispatch, and the post-run audit were outside those integrations.

The first integration attempts for both cases stopped before registration. My independent guard interpreted a descriptor-relative `runtime` directory name relative to the checkout's working directory. It refused fixture setup and cleanup. I preserved the two exit-1 observations, then reran the same harness from `/` with absolute script paths and fresh invented roots. Both corrected harness processes exited zero on their expected worker refusals. The two early fixture paths were never returned by the fixture generator and were not searched for or deleted. These were harness failures, separate from product findings.

The implementation critic independently reports that the same freeze accepted missing or incorrect ownership evidence, stale parent binding, wall-clock expiry and an LA-day change before broker entry. Its witnesses also found terminal publication by a losing consumption attempt, cleanup reported as reaped after expiry, and nested registration work continuing until control returned to the parent. I attribute these witnesses to the critic. My refusal probes did not exercise them. Until corrected and rechecked, neither this report nor the 59 passing component tests supports using this freeze for a paid cycle. The earlier independent auditor review also withholds actual-use clearance for its own freeze.

## Exact identities

Reviewer `/root/access_v2_quality` observed repository HEAD `31961555d2a698e43acb8f3de728917e390fed9c`. All four joint source/test hashes matched before and after execution. The approved registration freeze, controller/tests and 33 public source/dependency pins matched. Registration and worker children used the pinned Python 3.11.9 interpreter with `-I -S -B`. The outer pytest harness used the project's Python 3.13 environment.

| Artifact | SHA-256 |
| --- | --- |
| Joint freeze | `bd3f8ca4801c980c1fde88b385649bdf49291cea3af86e0db1a69eb3978c4804` |
| Producer report | `1c3e80c9445be3f9740be1015239a78d251083cbd2d8751da174d3598dcb8b2a` |
| Supervisor / supervisor tests | `1fb79f5735ce6ecbb5d7d026e11ee33c59773d13af7c72e3584547ff03404bcd` / `385dbc0f42c873c914698c8be542e2cc03cffbae2d3c67a8ae6212d2e3a5cf36` |
| Worker / worker tests | `7aa4e43c5a4453fad118d29f379fd5b1ba08d2b0cd5af0a955e2baa2c106c883` / `27c62e3b323c2d2dd585033eea0263c6098793ff92006174383eed9309619247` |
| Registration v2 freeze / controller | `da2db83c28e465345bb74c59e479fcf4fef233d6af8ef2d7406c26c59144fe38` / `3f52a95452d9a20c6c456624f33a70c717d9f1fc28d83ae65f178e67e9d7047d` |
| Combined test log | `b5741f7cdae03e9af1048fab4d2eb88cb2d5722670ca3865d0f18064cb71b8e9` |
| Paused / missing-key integration records | `de64a6881de6545423b148fd9fc617f3da7b93ba5ae94cbbc79b6faf3ca3f6e8` / `ad10aa7bff5b8f9ccfef83da8356ed5f2698aa73af9dedb8f70e08d2b146149f` |
| Aggregate quality evidence | `76702bec72e5392495805d53bbe44fa92241be2a95eeabd6f809dd9664fbd2c1` |

Commands, source copies, response-independent observers, stored synthetic fixtures and hashes are retained in ignored `runtime/development-cycle-launch-quality/`. No actual private inputs, credentials, market databases or old operational controllers were used. The corrected integration processes and their owned registration and worker children are terminal.
