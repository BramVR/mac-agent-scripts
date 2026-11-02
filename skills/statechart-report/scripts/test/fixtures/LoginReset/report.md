# LoginReset

TLC reached 9 states and 18 steps. The chart draws 9 states and 14 arrows.
With VIEW, TLC keeps one representative for each group of states that it counts as the same. An arrow can lead to the representative rather than to the state that the step reaches.

## NoResetEmail breaks
The shortest path has 2 steps:
0. Signed out
1. YouSubmitAPassword: Trying to sign in / Checking first try
2. YouTapForgotPassword: Reset email sent

## Rules that hold
TypeOK, NoDeadlock
