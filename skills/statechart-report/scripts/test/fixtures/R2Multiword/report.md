# CounterLoop

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

## ReachesThree breaks
TLC's counterexample is in tlc-ReachesThree.out. It has 3 steps:
0. Current count 0
1. Up: Current count 1
2. Up: Current count 2
3. Back: Current count 1
The run loops through "Current count 1" and "Current count 2" forever.

## Rules that hold
NoDeadlock
