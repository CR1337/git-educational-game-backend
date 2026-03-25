# Level Template Structure

## map.txt

```
3 3
###
#.#
###
1 1 *
```

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