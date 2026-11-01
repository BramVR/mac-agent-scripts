# CounterLoop

TLC reached 3 states and 3 steps. The chart draws 2 states and 3 arrows.

## ReachesThree breaks
TLC's counterexample is in tlc-ReachesThree.out. It has 3 steps:
0. Low
1. Up: Low
2. Up: High
3. Back: Low
The run loops through "Low" and "High" forever.

## Rules that hold
NoDeadlock
