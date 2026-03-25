# Puzzle

## Parameters

|Type|Description|Values|
|-|-|-|
|Direction (d)|Describes a direction on the map|left, right, up, down, below|
|Number (n)|An integer|0, 1, 2, 3|
|Tile (t)|A tile type|robot, walkable, pushable, hot, cold, energized|

## Commands

### Movement

|Command|Description|
|-|-|
|move d|move (and push) in direction d|
|dash d|move (and push) two tiles in direction d, costs energy|

### Iteraction

|Command|Description|
|-|-|
|pick d|pick up item in direction d|
|drop d|drop item i direction d|
|burn d|generates heat in direction d, costs energy|
|recylce d| recycles trash in direction d|

### Program flow

|Command|Description|
|-|-|
|wait [n]|do nothing [for n ticks]|
|yield [n]|pass controll flow to next robot [or to robot n]|
|halt|stop program execution completely|
|label n|declares the label n|
|test d t|sets internal flag to true if neighbor in direction d is tile type t else false|
|jump n|unconditionally jump to label n|
|jump_if n|jump to label n if internal flag is true|
|jump_if_not n|jump to label n if internal flag is false|

### Memory
|Command|Description|
|-|-|
|set|sets internal flag to true|
|clear|sets internal flag to false|
|toggle|toggles internal flag|

### Signals
|Command|Description|
|-|-|
|signal n|sends the signal n|
|listen n|waits until signal n is received|
|poll n|sets internal flag to true if signal n was received else false|
|clear_signals|clear all received signals|

## Map

|Tile|Description|Pushable|
|-|-|-|
|0-3|robots 0-3|yes|
|.|empty tile|Empty|no|
|#|wall - cannot be walked on or pushed|no|
|=|pushable box - can be pushed|yes|
|$|source - must be pushed to destination|yes|
|!|destination - win when sources stand an a destination|no|
|<|left conveyer - moves pushables to the left|no|
|>|right conveyer - moves pushables to the right|no|
|^|up conveyer - moves pushables up|no|
|v|down conveyer - moves pushables down|no|
|K|key - opens a lock if a robot carrying it walks onto the lock|no|
|L|lock - see key|no|
|w-z|pressure plates - holds open corresponding door when pushable stands on it|no|
|W-Z|doors - see pressure plates|no|

|~|ice - pushables glide on it, can be melted|no|
|*|ice block - cannot be passed until melted|no|
|B|battery - robot can perform one energy requireing command|
|E|power supply - robot can perform energy requireing commands while neighboring|
|b|trash - turns into fire when burned, vanishes when recycled|no|
|f|fire - melts neighboring ice, burns neighboring trash, vanishes|no| 


|4-8|bomb - burns the neighbors after 4-8 ticks after activation, activated by burning or energizing|yes|
|h,j,k,l|power plant - drops battery in corresponding direction when heated for 3 ticks|

### Example Map

```
16 16
################
#..............#
#.w............#
#..............#
#..............#
#............W.#
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
#..............#
################
2 2 *
```

