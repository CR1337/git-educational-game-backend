# Git Communication

## Local

### Non-Editor Command

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant git

    activate User

    User ->>+ git: argv
    git -->>- User: stdout, stderr, returncode

    deactivate User
```

### Editor Command

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant git
    participant Editor

    activate User

    User ->>+ git: argv
        git ->>+ Editor: filename
            Editor ->>+ User: editor windows opens
            User -->>- Editor: new content
        Editor -->>- git: returncode
    git -->>- User: stdout, stderr, returncode

    deactivate User
```

## Client-Server

### Non-Editor Command

```mermaid
sequenceDiagram
    autonumber
    participant Client

    activate Client
    
    create participant Server
    Client ->>+ Server: POST /git-command (argv)

        create participant Worker
        Server ->>+ Worker: argv

            create participant git
            Worker ->>+ git: argv

            git -->>- Worker: stdout, stderr, status

        Worker -->>- Server: stdout, stderr, status

    Server -->>- Client: 200 OK (stdout, stderr, status)

    deactivate Client
```

### Editor Command

```mermaid
sequenceDiagram
    autonumber
    participant Client

    activate Client

    create participant Server1
    Client ->> Server1: POST /git-command (argv)
    activate Server1

        create participant Worker
        Server1 ->> Worker: argv
        activate Worker

            create participant git
            Worker ->> git: argv
            activate git

                create participant Editor
                git ->> Editor: filename
                activate Editor

            Editor --) Worker: filename, content

        Worker --) Server1: filename, content

    Server1 -->> Client: 200 OK (filename, content)
    deactivate Server1

    create participant Server2
    Client ->> Server2: POST /editor-response (new_content, abort)
    activate Server2

        Server2 --) Worker: new_content, abort

            Worker --) Editor: new_content, abort

                Editor -->> git: returncode
                deactivate Editor

            git -->> Worker: stdout, stderr, status
            deactivate git

        Worker -->> Server2: stdout, stderr, status
        deactivate Worker

    Server2 -->> Client: 200 OK (stdout, stderr, status)
    deactivate Server2

    deactivate Client
```

### Non-Editor Command with Orchestrator

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Orchestrator

    activate Client
    activate Orchestrator
    
    create participant Server
    Client ->> Server: POST /git-command (argv)
    activate Server

        Server --) Orchestrator: argv

            create participant git
            Orchestrator ->> git: argv
            activate git

            git -->> Orchestrator: stdout, stderr, status
            deactivate git

        Orchestrator --) Server: stdout, stderr, status

    Server -->> Client: 200 OK (stdout, stderr, status)
    deactivate Server

    deactivate Orchestrator
    deactivate Client
```

### Editor Command with Orchestrator

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Orchestrator

    activate Client
    activate Orchestrator

    create participant Server1
    Client ->> Server1: POST /git-command (argv)
    activate Server1

        Server1 --) Orchestrator: argv

            create participant git
            Orchestrator ->> git: argv
            activate git

                create participant Editor
                git ->> Editor: filename
                activate Editor

            Editor --) Orchestrator: filename, content

        Orchestrator --) Server1: filename, content

    Server1 -->> Client: 200 OK (filename, content)
    deactivate Server1

    create participant Server2
    Client ->> Server2: POST /editor-response (new_content, abort)
    activate Server2

        Server2 --) Orchestrator: new_content, abort

            Orchestrator --) Editor: new_content, abort

                Editor -->> git: returncode
                deactivate Editor

            git -->> Orchestrator: stdout, stderr, status
            deactivate git

        Orchestrator --) Server2: stdout, stderr, status

    Server2 -->> Client: 200 OK (stdout, stderr, status)
    deactivate Server2

    deactivate Orchestrator
    deactivate Client
```