# O'Neil/IBD Technical Source Lock v1

No performance result was consulted.

## Entry

Entry remains separated into original O'Neil/IBD breakout concepts and the USSY
causal T+1 Open operationalization.

## Exit — verified official IBD evidence

Retrieval date: 2026-09-19.

- **Defensive loss — ORIGINAL.** Current IBD guidance treats 7% below actual
  purchase price as the practical maximum-loss trigger. Older IBD material often
  described 7-8%. Core v1.1 therefore uses 7% from the actual USSY fill.
  Source: https://www.investors.com/how-to-invest/investors-corner/how-to-sell-stocks-sell-rule-profiting-from-metas-328-crash-and-148-gain/

- **Normal profit zone — ORIGINAL.** The ordinary profit-taking zone is roughly
  20-25% above the ideal/proper buy point, not above the investor's actual fill.
  Source: https://www.investors.com/how-to-invest/when-to-sell-stocks/

- **Eight-week hold exception — ORIGINAL and material.** If a stock gains more
  than 20% from the ideal buy point within three weeks of a proper breakout,
  IBD says to hold it for at least eight weeks; breakout week counts as week 1.
  Therefore unconditional machine exit at +20% is not source-faithful.
  Source: https://www.investors.com/how-to-invest/when-to-sell-stocks/

- **10-week line on heavy volume — ORIGINAL technical sell evidence.** Official
  MarketSmith/IBD educational material describes a first drop below the 10-week
  line on big volume as a sell rule. Core's completed-week close below 10W MA
  with above-average volume is an explicit machine operationalization.
  Source: https://marketsurge-files.investors.com/2020/04/stockguide-Q2-2018.pdf

## Core v1.1 correction

Until rapid-winner qualification and the eight-week clock are represented as
causal persistent position state, `NORMAL_PROFIT_ZONE` is evidence-only and
non-actionable. This fails closed rather than silently violating the exception.

The defensive trigger is corrected from the earlier 8% operationalization to
the current practical IBD 7% maximum-loss trigger.

Core has no generic max-hold. The eight-week rule is a methodology-specific
exception for qualifying rapid winners, not a generic time exit.

## Deferred

Until direct deterministic source specification and required state are frozen:

- actionable 20-25% profit taking with eight-week exception;
- exact round-trip action;
- climax-top automation;
- upper-channel-line automation;
- largest-one-day-decline standalone action;
- composite deterioration scoring.

These may remain evidence-only; they may not silently become exit actions.
