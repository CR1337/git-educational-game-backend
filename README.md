# git-educational-game-backend

## Setup (Linux only)

1. Install [docker](https://docs.docker.com/engine/install/) or [podman](https://podman.io/docs/installation).

2. Place the exported game files into `volumes/game/`.

3. Run `chmod +x setup.sh`

4. Run `./setup.sh` and follow the instructions.

5. Run the containers

```bash
bin/run
```

6. Test that it works.

```bash
bin/test
```

7. The game is now available at [http://localhost:8080/game](http://localhost:8080/game). The API ist available at [http://localhost:8080/api](http://localhost:8080/api).


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