import sys
import daemon

from git_orchestrator.git_orchestrator import GitOrchestrator


def main() -> None:
    run_as_daemon = len(sys.argv) > 1 and sys.argv[1] == "--daemon"
    
    if run_as_daemon:
        print("Starting Git Orchestrator daemonized", flush=True)
        with daemon.DaemonContext():
            orchestrator = GitOrchestrator()
            orchestrator.run()

    else:
        print("Starting Git Orchestrator", flush=True)
        orchestrator = GitOrchestrator()
        orchestrator.run()


if __name__ == "__main__":
    main()  
