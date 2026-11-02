# D007 independent exchange-calendar check

**Nasdaq's published schedule yields 50 regular-session dates from May 1 through July 12, 2024, inclusive: 22 in May, 19 in June and 9 through July 12. July 3 remains a session with an early close.** Friday June 7 and Monday June 10 are adjacent scheduled sessions.

Checked 2026-11-02 UTC without provider data, private market records, runtime files or credentials. The public derived list is `/tmp/d007-nasdaq-2024-sessions.json`; root handles retained-source receipts separately.

## Actual visual inspection

I directly downloaded the official [Nasdaq Trading Calendar 2024](https://www.nasdaqtrader.com/content/technicalsupport/2024tradingcalendar.pdf): 105,969 bytes, SHA-256 `5a417265c706abe1e2eaa24e0c1fde1787e79fdd472eca105466a019f8ff1101`. I rendered its single page locally with Poppler at 150 dpi and inspected the full image. The web screenshot endpoint returned a reference without image pixels; the actual visual check used the local rendering.

Page 1's HOLIDAYS legend identifies filled orange circles as exchange holidays and hollow orange circles as 1 PM ET closes. Saturday/Sunday occupy blue-shaded columns. In the May/June/July grids, May 27, June 19 and July 4 have filled orange markers; July 3 has the hollow marker. June 7's burgundy marker concerns an index announcement, not a closure. June 8–9 occupy weekend columns, and June 10 has no holiday marker. Thus June 10 is the next scheduled session after June 7.

I enumerated Monday–Friday dates in the inclusive interval, excluded the three marked holidays and retained July 3. This construction produced the JSON list independently of Alpaca or any other provider calendar.

## Dated holiday corroboration

The alerts' “U.S. Equities and Options” sections independently confirm the relevant exceptions:

- [ETA2024-28, May 13, 2024](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-28): May 27 closure for Memorial Day.
- [ETA2024-33, June 4, 2024](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-33): June 19 closure for Juneteenth.
- [ETA2024-36, June 13, 2024](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-36): July 4 closure and July 3 early close.

The calendar supplies the specific 1 PM ET close; the July alert corroborates that July 3 is shortened rather than closed.

## Evidentiary limit

This is an independent extraction of the published Nasdaq US-equity schedule. It supports scheduled event adjacency and a date-for-date comparison with a provider calendar. It does not universally establish absence of emergency closures, symbol-specific halts, missing bars or settlement exceptions. Nor does it itself establish that the split occurred: that judgment still requires the separate issuer evidence. An early-close session belongs in the session count, but its shorter duration must remain available to later intraday or execution models.
