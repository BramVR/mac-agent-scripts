# OrLoop

TLC reached 4 states and 5 steps. The chart draws 2 states and 3 arrows.
The chart does not draw 1 steps that stay in one chart state.

## ReachesNine breaks
TLC's counterexample is in tlc-ReachesNine.out. It has 2 steps:
0. Low
1. you add one or more: Low
2. the clock ticks: Low
The run stays in "Low" forever.

## Rules that hold
NoDeadlock
