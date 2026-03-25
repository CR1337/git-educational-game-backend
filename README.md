# git-educational-game-backend

## Setup

1. [Install docker](https://docs.docker.com/engine/install/).

2. Place the exported game files into `volumes/game/`.

_(The game is still in development. Until then a placeholder `index.html` is used.)_

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

## Advanced

You can stop the docker containers with 

```bash
bin/stop
```

---

With

```bash
bin/run -i
```

you can see the containers output in the terminal.

---

When everything is running you can try the API manually at [http://localhost:8080/api/docs](http://localhost:8080/api/docs).