# Exit Arbitration v1

This contract resolves the interaction between the ordinary 20-25% profit zone,
the rapid-winner eight-week exception, defensive loss, and independent technical
sell evidence.

Rules:

1. A qualifying eight-week hold blocks **ordinary profit-taking** while its
   minimum hold is active.
2. It does **not** block the source-locked defensive-loss rule.
3. It does **not** block independent source-locked technical sell evidence such
   as the implemented weekly 10-week-line violation.
4. During weeks 1-3, a position in the profit zone that has not yet qualified is
   held until the rapid-winner qualification window is resolved.
5. If week 3 passes without qualification, normal profit-zone evidence may act.
6. For a qualified rapid winner, normal profit-zone evidence may act after the
   minimum eight-week hold is complete.
7. Multiple simultaneous independent actionable exits fail closed rather than
   receiving an invented priority.

This is not a generic max-hold. Completion of eight weeks does not itself create
a sell signal; it only removes the rapid-winner block on otherwise valid profit
taking.
