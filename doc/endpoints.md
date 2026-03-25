# Backend endpoints

## Level endpoints

These endpoints static level data.

### `GET /levels`

Returns a list of all level ids

### `GET /levels/{level-id}`

Returns a level object with level-id

### Example of a level object

```json
{
    "name": "Level 1",
    "files": [
        "filename1",
        "filename2",
        "filename3"
    ]
}
```

## Game endpoints

These endpoints return dynamic level data and game data.

### `GET /games`

Returns a list of all game ids.

### `POST /games/new`

Creates a new game and returns the game object

### `GET /games/{game-id}`

Returns a game object with game-id

### `DELETE /games/{game-id}`

Deletes a game from the server.