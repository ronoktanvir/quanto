# D008 paid child integration correction

The corrected child addresses the lead's environment, deadline and evidence-chain findings. It remains preparation only: no actual entrypoint, private input, model credential, store, network call or paid cycle was executed. Independent combined review is still required.

The original [preparation report](D008-paid-worker-preparation.md) and first source/tests are preserved byte-for-byte. The additional frozen copies are under ignored `runtime/development-cycle-launch-preparation/paid-worker-v1-frozen/`. The first source's blanket empty-environment check would refuse the reviewed interpreter on this Mac because Python supplies narrowly defined locale/encoding variables. Its receipts also did not bind the complete prelaunch ancestry, its child relied on the parent for timeout enforcement, and failed bootstrap could attempt publication in the fixed actual state directory. Those limitations make that first version unsuitable for actual use.

## Corrected controls

The environment check now follows registration v2: only `LC_CTYPE` and `__CF_USER_TEXT_ENCODING` may exist; locale must be `C.UTF-8` or `UTF-8`, and encoding must match the accepted hexadecimal tuple. Isolated mode, no site loading and no bytecode writing remain required. Every other environment name or malformed value is refused. The authenticated supervisor subsequently enforces the exact reviewed interpreter and source pins.

After successful authenticated bootstrap, `run()` arms a child-side alarm for the remaining absolute monotonic deadline returned by `worker_context()`, before product activity. A fixed exception ends the child path; the previous handler/timer is restored without granting its original elapsed interval again. Post-state observations first check the same deadline, and the parent retains separate process cleanup responsibility. Failed bootstrap leaves the state destination unset, so its failure path cannot write actual outcome or terminal files.

The exclusive call-entry receipt now joins the request hash, exact registration-result hash, `paid-consumed.json`, supervisor `consumed.json`, `paid-launch.json`, the exclusive six-field `prelaunch.json` and the new budget observation. These inputs are reread and compared before the call. The registration result's canonical digest must equal the launch-bound digest, and both durable parent PIDs must match the actual parent. The clean terminal separately retains the prelaunch digest. The exact six-field prelaunch shape is unchanged.

`prelaunch-budget.json` records `day`, `observed_at`, `global_limit_micro_usd`, `global_remaining_micro_usd`, `purpose_limit_micro_usd`, `purpose_remaining_micro_usd`, `required_micro_usd` and `planning_only`. It requires the current Los Angeles day, USD20 global policy, USD4 research policy and USD2.625 remaining in both. Its digest enters the call-entry receipt. This is historical planning evidence, not an atomic reservation, concurrency exclusion or account-wide observation. The existing dispatch atomics retain authority over each actual call.

The call-profile deny list now uses the actual unrelated entry names `critic.request_review` and `provider.diagnose_operations`, alongside unrelated provider requests, acquisition entry functions and execution/Runpod modules. The funding and response path remains the unchanged broker with no injected transport.

## Verification and preserved failures

The final run passed **46 invented cases in 0.38 seconds**; Ruff passed. The added cases verify all call-entry digest links, unchanged prelaunch shape, separate budget observation, changed durable parent records, exact registration-result binding, no publication after failed bootstrap, alarm interruption/handler restoration, and actual forbidden function names. A subprocess using the reviewed Python 3.11 interpreter, `-I -S -B`, empty supplied environment and disabled stdin ran only the isolated environment preflight; it passed with this machine's interpreter-generated locale/encoding variables. It did not call `bootstrap()` or read actual state.

An intermediate regression run reported 10 failures and 21 passes because an older invented deadline was roughly 317 years into the future and exceeded this machine's timer range. The direct invented execution case passed; replacing that unrealistic fixture deadline with a finite one-hour window restored the positive alarm path. Subsequent 32-, 44-, 45- and 46-case runs passed. That failed invented run and the earlier first-version failures remain in the tool record. The producer did not mask or reinterpret an actual run failure.

The existing development interpreter runs pytest on Python 3.13. The reviewed 3.11 subprocess verifies the real minimal environment and public hermetic imports, not an actual paid workflow. Fake module and transport-free invented tests cannot establish provider responses, private-input readiness, independent numerical agreement or operational acceptance. Process death may leave charges/effects or incomplete receipts; the exact outcome and uncertainty behavior remain as described in the original report.

| Artifact | SHA-256 |
| --- | --- |
| Corrected `paid_worker.py` | `09afd6f6e2da6e293b912798a22c9611c12fd6d7bfc74d60b9948dc9e0cbb21f` |
| Corrected `test_paid_worker.py` | `99d61c6d42dbf2a96c5c0743136914ee37473dd0a4801b80adf022e35a5de4d5` |
| Preserved first child | `2630baf8802baf25ba7568d38f4d5801d920073ea1ec0ea0794be1dbc5b0f70f` |
| Preserved first tests | `05580e060b645783f77d0b98fc535425e7b69a4dd21c743304931ac833afc720` |
| Preserved first report | `c0c797b4c2e4829f1293772a3d1214e1c3c88963c064bdd45dccc75f283335fc` |

No product, Git or project-context edits occurred. The lead owns integration with the supervisor, auditor, reviewed private packet and separate criticism, quality and scope gates.
