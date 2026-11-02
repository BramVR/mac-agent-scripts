# CounterLoop

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

## ReachesThree breaks
TLC's counterexample is in tlc-ReachesThree.out. It has 3 steps:
0. Count Ready
1. you advance: now: Count Count Ready
2. you advance: now: Count Done
3. you advance: now: Count Count Ready
The run loops through "Count Count Ready" and "Count Done" forever.

## Rules that hold
NoDeadlock
