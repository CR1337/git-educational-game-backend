# git Communication

## Non-Editor git command

### Local

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant git

    User ->>+ git: argv, stdin
    git -->>- User: stdout, stderr, status
```
### Server

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Server
    participant git
    
    Client ->>+ Server: POST /git (argv, stdin)

        Server ->>+ git: argv, stdin

        git -->>- Server: stdout, stderr, status

    Server -->>- Client: 200 OK (stdout, stderr, status)
```

## Editor git command

### Local

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant git
    participant Editor

    User ->>+ git: argv, stdin
        git ->>+ Editor: filename
            Editor ->>+ User:
            User -->>- Editor:
        Editor -->>- git: status
    git -->>- User: stdout, stderr, status
```

### Server

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Server
    participant git
    participant EditorSimulator

    Client ->>+ Server: POST /git (argv, stdin)
        Server ->> git: argv, stdin
            activate git
            git ->> EditorSimulator: filename
        activate EditorSimulator
        EditorSimulator ->> Server: POST /editor-session/{session_id}/init (file_content)
    Server -->>- Client: 200 OK (session_id, file_content)

    Client ->>+ Server: POST /editor-session/{session_id} (edited_content)
        Server ->> EditorSimulator: edited_content
            EditorSimulator -->> git: 
            deactivate EditorSimulator


        git -->> Server: stdout, stderr, status
        deactivate git
    Server -->>- Client: 200 OK (stdout, stderr, status)
```

## git Orchestrator State Diagram

```mermaid
stateDiagram-v2
    direction LR

    [*] --> running

    state orchstrator_running {
        running --> wait_for_stdin: GIT_STDIN_READY
        running --> wait_for_editor_content: GIT_OPENED_EDITOR

        wait_for_stdin --> running: STDIN_FROM_SERVER

        wait_for_editor_content --> running: CONTENT_FROM_SERVER
    }
    
    running --> [*]: SIGCHLD

    orchstrator_running --> [*]: SIGTERM
```