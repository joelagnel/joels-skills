# ASCII Art Diagrams

**MANDATORY** for plain-text documentation. Use only ASCII characters (no Unicode box drawing).

## Box-and-Arrow Style

```
+------------------------------------------------------------------+
|                    Component Architecture                         |
+------------------------------------------------------------------+

  +----------------+        +----------------+        +----------------+
  |   Component A  |        |   Component B  |        |   Component C  |
  |                |------->|                |------->|                |
  | - feature 1    |        | - feature 1    |        | - feature 1    |
  | - feature 2    |        | - feature 2    |        | - feature 2    |
  +----------------+        +----------------+        +----------------+
         |                         ^
         |                         |
         +-------------------------+
               feedback loop
```

## Data Structure Layout

```
struct task_queue:

  head
    |
    v
+-----+    +-----+    +-----+    +-----+    +-----+
|Task |--->|Task |--->|Task |--->|Task |--->|Task |---> NULL
+-----+    +-----+    +-----+    +-----+    +-----+
    ^          ^          ^          ^          ^
    |          |          |          |          |
tails[0]   tails[1]   tails[2]              tails[3]
 DONE       WAIT       READY                 NEW
```

## State Machine

```
                    +------------------+
                    |      IDLE        |
                    +--------+---------+
                             |
                    [event: start]
                             |
                             v
                    +------------------+
                    |     RUNNING      |<--------+
                    +--------+---------+         |
                             |                   |
            +----------------+----------------+  |
            |                                 |  |
     [event: pause]                   [event: resume]
            |                                 |  |
            v                                 |  |
    +------------------+                      |  |
    |     PAUSED       |----------------------+  |
    +--------+---------+                         |
             |                                   |
      [event: stop]                              |
             |                                   |
             v                                   |
    +------------------+                         |
    |     STOPPED      |-------------------------+
    +------------------+       [event: restart]
```

## Timeline/Event Diagram

```
Timeline:
=========

Worker 0: [busy] ......... [idle] .............
Worker 1: ......... [busy] ......... [idle] ...
Worker 2: [idle] ..............................
         ^                                    ^
         |                                    |
   Batch starts                         Batch ends
         |<---- Batch Window ---->|
```

## Decision Tree

```
                         +-------------+
                         | Start       |
                         +------+------+
                                |
                         +------v------+
                         | Condition A |
                         +------+------+
                                |
               +----------------+----------------+
               |                                 |
              YES                               NO
               |                                 |
        +------v------+                   +------v------+
        | Action X    |                   | Condition B |
        +-------------+                   +------+------+
                                                 |
                                    +------------+------------+
                                    |                         |
                                   YES                       NO
                                    |                         |
                             +------v------+           +------v------+
                             | Action Y    |           | Action Z    |
                             +-------------+           +-------------+
```

## Best Practices

1. Use only these characters: `+ - | / \ ^ v > < = [ ] ( ) . _ : # * ~ ` (and space)
2. Align boxes horizontally and vertically.
3. Use consistent spacing (typically 4 spaces between elements).
4. Add labels above or below arrows, not on them.
5. Keep diagrams under 80 characters wide for terminal compatibility.
6. Use `.` or `...` for spacing in timelines.
7. Use indentation to show hierarchy.

## Character Reference

```
Box corners:    + + + +
Horizontal:     - = _
Vertical:       |
Arrows:         -> <- v ^ --> <--
Connections:    / \
Lists:          [ ] ( ) { }
Continuation:   ... ~~~
```

## Memory Layout Example

```
+---------------------------------------------------------------+
|                         task_queue                            |
+---------------------------------------------------------------+
| head -> [T] -> [T] -> [T] -> [T] -> [T] -> NULL               |
|          ^        ^            ^            ^                 |
|          |        |            |            |                 |
|     DONE_TAIL  WAIT_TAIL   READY_TAIL   NEW_TAIL             |
|                                                               |
| seglen[0..3]: Count of tasks in each segment                  |
| batch[0..3]:  Batch number when segment becomes ready         |
+---------------------------------------------------------------+
```

## Call Flow (Vertical)

```
caller()
    |
    v
+-------------------+
| function_a()      |
|   - step 1        |
|   - step 2        |
+-------------------+
    |
    v
+-------------------+
| function_b()      |
|   - step 1        |
+-------------------+
    |
    v
+-------------------+
| function_c()      |
+-------------------+
```
