# CounterLoop

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

## ReachesThree breaks
TLC's counterexample is in tlc-ReachesThree.out. It has 3 steps:
0. Count 0
1. Up: Count 1
2. Up: Count 2
3. Back: Count 1
The run loops through "Count 1" and "Count 2" forever.

## Rules that hold
NoDeadlock
