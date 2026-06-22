# Level Representation

## map.txt

```
3 3
###
#.#
###
1 1 1
```

|Line  |Description                                                       |
|------|------------------------------------------------------------------|
|1     |Width (w) and Height (h) of the map.                              |
|2..h+1|Immovable tiles arranged in a 2d grid.                            |
|h+2.. |Each line contains an x position, a y position and a movable tile.|


## text.json

```json
{
    "intro": "string",
    "outro": "string",
    "clues": []
}
```

## meta.json

```json
{
    "id": "string",
    "name": "string",
    "successor": "string"
}
```

## files/*.bot

```
# used commands
move right
# available commands
move left
```

## init.lst

```
git ...
write <source> <destination>
remove <filename>
create <filename>
# ...
```