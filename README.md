# git-educational-game-backend

## Setup

1. [Install docker](https://docs.docker.com/engine/install/).

2. Place the exported game files into `volumes/game/`.

3. Build the docker images.

```bash
bin/build
```

4. Run the docker containers

```bash
bin/run
```

5. Test that it works.

```bash
bin/test
```

6. The game is now available at [http://localhost:8080/game](http://localhost:8080/game). The API ist available at [http://localhost:8080/api](http://localhost:8080/api).

