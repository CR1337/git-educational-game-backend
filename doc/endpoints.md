# Backend endpoints


## Level endpoints

### GET `/levels`

### GET `/levels/{level-id}`


## Game endpoints

### GET `/games`

### GET `/games/{game-id}`

### DELETE `/games/{game-id}`

### POST `/games/new`

### POST `/games/{game-id}/run-tests/{level-id}`

### GET `/games/{game-id}/progress`


## Filesystem endpoints

### GET `/games/{game-id}/files/{filepath}`

### POST `/games/{game-id}/files/{filepath}`

### PUT `/games/{game-id}/files/{filepath}`

### DELETE `/games/{game-id}/files/{filepath}`

### GET `/games/{game-id}/current-working-directory`

### PUT `/games/{game-id}/current-working-directory`


## Git endpoints

### POST `/games/git`

### POST `/games/git/editor-session/new`

### POST `/games/git/editor-session/{editor-session-id}`
