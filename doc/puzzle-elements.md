 # Level Elements

## Tiles

|Symbol|Name       |Description                                                                    |Movable|
|------|-----------|-------------------------------------------------------------------------------|-------|
| 1-4  |Robots     |Robots are controlled by the players programs.                                 |yes    |
|   +  |Box        |A Box can be pushed by a Robot.                                                |yes    |
| 5-8  |Mark       |These can be placed, removed and read by Robots. Each ribit has its own type   |yes    |
|   .  |Empty      |This is an empty tile.                                                         |no     |
|   #  |Wall       |A Wall is an immovable object.                                                 |no     |
|   *  |Destination|The Level is solved when each destination has a box on it.                     |no     |
| a-p  |Buttons    |A Button opens the corresponding door(s) when a Robot or a Box is placed on it.|no     |
| A-P  |Doors      |See Buttons.                                                                   |no     |

## Programs

### Parameter Types

|Type         |Values            |Description                                 |
|-------------|------------------|--------------------------------------------|
|TurnDirection|L, R              |The directions Left and Right               |
|Direction    |L, R, F, B        |The directions Left, Right, Front and Below.|
|Tile         |(all of the tiles)|All of the tiles.                           |
|Number       |0-255             |A number between 0 and 255.                 |

### Commands

Each Robot has two one bit registers A and B.

|Category|Menmonic|Parameter          |Description|
|--------|--------|-------------------|-----------------------------------------------------------------------|
|Movement|Move    |                   |Move one tile forward.                                                 |
|        |Turn    |TurnDirection      |Turn in the direction.                                                 |
|Marks   |Put     |Direction          |Put a mark on the tile in the direction.                               |
|        |Remove  |                   |Remove a mark from the Tile in the direction.                          |
|Scanning|Scan    |Diretion, Tile     |Write 1 to A if there is the tile in that direction, else write 0 to A.|
|Memory  |Set     |                   |Set A to 1.                                                            |
|        |Clear   |                   |Set A to 0.                                                            |
|        |Toggle  |                   |Toggle the value in A.                                                 |
|        |Random  |                   |Set A to a random value.                                               |
|        |Swap    |                   |Swap the contents of A and B.                                          |
|Jumps   |Label   |Number             |Declare a label.                                                       |
|        |Jump    |Number             |Jump to the label.                                                     |
|        |Branch  |Number             |Jump to the label if A is 1.                                           |