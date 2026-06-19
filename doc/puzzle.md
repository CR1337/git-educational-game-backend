# Puzzle

## Parameters

|Type         |Decription             |Values                                                                  |
|-------------|-----------------------|------------------------------------------------------------------------|
|Direction (d)|A direcrtion on the map|north, west, east, south, here                                          |
|Number (n)   |An integer             |0, 1, 2, 3                                                              |
|Tile (t)     |A tile type            |Robot, Empty, Pushable, Solid, Item, Interactable, <specific tile type> |

## Commands

### Movement

|Command|Description                   |
|-------|------------------------------|
|move d |move (and push) in direction d|

### Interaction

|Command   |Description                                                         |
|----------|--------------------------------------------------------------------|
|pick d    |pick up item indirection d                                          |
|drop d    |drop item in direction d                                            |
|scan d t n|set flag n to 1 if tile in direction d is of type t else set it to 0|

### Memory

|Command |Description    |
|--------|---------------|
|set n   |set flag n to 1|
|clear n |set flag n to 0|
|toggle n|toggle flag n  |

### Signals

|Command   |Description                                                   |
|----------|--------------------------------------------------------------|
|signal n  |send signal n                                                 |
|listen n  |wait until signal n was received                              |
|poll n1 n2|set flag n2 to the state of signal n1, then set signal n1 to 0|

### Waiting

|Command|Description                    |
|-------|-------------------------------|
|wait   |do nothing                     |
|next   |pass control to the next robot |
|yield n|pass control to robot n        |
|halt   |stop program execution entirely|

### Program Flow

|Command      |Description                     |
|-------------|--------------------------------|
|label n      |declare a label called n        |
|jump n       |unconditionally jump to label n |
|jump_if n1 n2|jump to label n1 of flag n2 is 1|

## Tiles

|Symbol|Name             |Type                |Layer|Description                                                                                            |
|------|-----------------|--------------------|-----|-------------------------------------------------------------------------------------------------------|
|0-3   |Robot            |Robot               |    1|One of four robots.                                                                                    |
|.     |Empty tile       |Empty               |    0|An empty tile.                                                                                         |
|#     |Wall             |Solid               |    0|A solid wall.                                                                                          |
|=     |Box              |Pushable            |    1|A box that can be pushed.                                                                              |
|$     |Source           |Pushable            |    1|A special object that can be pushed.                                                                   |
|!     |Destination      |Empty               |    0|The destination for special objects to be pushed on. To win all sources must be pushed to destinations.|
|?     |Subgoal          |Empty               |    0|A sub destination for special objects to be pushed on which toggles the activation of the subgoal.     |
|&     |Activated subgoal|Empty               |    0|To win all subgoals must be activated.                                                                 |
|K     |Key              |Item                |    1|Can be picked up to open a lock.                                                                       |
|L     |Lock             |Interactable, Solid |    1|Can be opened by dropping a key on it.                                                                 |
|w-z   |Pressure Plate   |Interactable        |    0|Opens the corresponding door by placing a robot or a pushable on it.                                   |
|W-Z   |Door             |Solid               |    1|Is opened by the corresponding pressure plate.                                                         |
|<     |Left conveyer    |Empty               |    0|Moves an robot or pusshable to the left.                                                               |
|>     |Right conveyer   |Empty               |    0|Moves an robot or pusshable to the right.                                                              |
|^     |Up conveyer      |Empty               |    0|Moves an robot or pusshable to up.                                                                     |
|v     |Down conveyer    |Empty               |    0|Moves an robot or pusshable to down.                                                                   |