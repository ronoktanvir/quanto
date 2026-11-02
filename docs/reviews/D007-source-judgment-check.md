# D007 concrete source-judgment check

**The proposed issuer facts and explicitly attributed purchaser-entitlement inference support the narrow economic-share proposal, with the source and model qualifications below.** They do not certify vendor dates, actual broker delivery or implementation. Checked 2026-11-02 UTC against public sources accessed directly through the web tool; no private vendor records, runtime objects, credentials or code were inspected or changed.

## Directly supported issuer extraction

[NVIDIA's June 2024 FAQ](https://s201.q4cdn.com/141608511/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf) supports:

- Questions 1 and 5, page 1: common-stock ten-for-one forward split; June 6, 2024 close as record boundary; nine additional shares distributed after the June 7 close.
- Questions 5 and 10, pages 1–2: **expected** split-adjusted trading at the June 10 market open. Preserve that evidentiary wording; it is not an exchange confirmation of completed trading. Question 17, page 3, describes June 10 availability as scheduled.
- Question 18, page 3: a shareholder selling on or before June 7 does not receive the additional shares regardless of settlement date. This directly supports the proposed seller statement.
- Questions 12 and 15, page 2: brokerage processes can vary; NVIDIA does not issue fractional shares. Thus account availability and broker fractional treatment cannot be inferred from the economic transformation.

The proposed extraction is accurate. Its June 10 boundary should retain the issuer's expected/scheduled attribution. The separate June 11 ex-dividend date in question 10 concerns the cash dividend, not split trading.

## Attributed inference and accounting boundary

[FINRA 11630](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11630), (a), describes a due-bill as evidence of security-right transfer or a seller's delivery obligation to a subsequent purchaser. Paragraph (c) addresses securities sold before ex status but delivered too late for record registration; (e) and (f) address redemption and failure. Together with the event-specific seller statement, these provisions support the interpretation that an ordinary pre-boundary purchaser carries the attached split entitlement, including a trade after record date. That is an inference, not a direct NVIDIA purchaser quotation or proof that every trade settled normally.

Transforming economic holdings once before the first adjusted regular session is consistent with that inference: pre-boundary holdings represent the shares plus attached split interest, and the transformation expresses the combined interest in new share units. Do not credit a second distribution at record, payable or redemption. This conclusion assumes ordinary regular-way terms and timely ordinary settlement. It does not model the payment proration described in 11630(c), broker buying power, fails or delivery delays; resulting cash is modeled economic cash rather than certified spendable brokerage cash.

[FINRA 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140), (a), (b)(2) and (c), supports using designated ex/trading dates and recognizes exceptional timing. [Notice 24-04](https://www.finra.org/rules-guidance/notices/24-04), “Operative Date” and discussion of Rule 11140, places the T+1 change on May 28, 2024. June falls after that change; this check grants no retrospective application to older settlement regimes.

## Provider disputes and evidence limits

The [pinned Alpaca schema](https://raw.githubusercontent.com/alpacahq/cli/709d11400129dc7c09b41dd05263187e15801a71/api/specs/market-data-api.json), `components.schemas.{record_date,payable_date,process_date,due_bill_redemption_date,ex_date}`, supplies generic descriptions, not an event-specific reconciliation. Any vendor record/payable differences must remain unresolved. They can sit outside the accepted model only when independent primary evidence establishes identity, ratio, trading boundary and ordinary entitlement without using those disputed fields, and the disagreement does not undermine those facts. Do not claim different semantics explain it; refuse when the dispute affects a controlling fact or requires an unmodeled claim.

My earlier adviser report accessed OCC memorandum 54623 through web extraction. That is not retained-byte verification. Root now reports direct preservation returned 403 and web access timed out; I did not retry or rely on OCC here, and no retained OCC bytes are claimed. Root-reported FAQ and Q2-filing mirror hashes were not independently read or verified in this check. This assessment rests on the directly accessed FAQ, rules and pinned schema, not that mirror or an exchange completion certificate.
