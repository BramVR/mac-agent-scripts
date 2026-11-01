# CounterLoop

TLC reached 3 states and 3 steps. The chart draws 1 states and 1 arrows.

## ReachesThree breaks
TLC's counterexample is in tlc-ReachesThree.out. It has 3 steps:
0. Busy
1. Up: Busy
2. Up: Busy
3. Back: Busy
The run stays in "Busy" forever.

## Rules that hold
NoDeadlock
