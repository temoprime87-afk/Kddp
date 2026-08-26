
from agents.orchestrator import Orchestrator


def main():
    print("")
    print("========================================")
    print("        KDP AUTONOMOUS AGENT")
    print("========================================")
    print("")

    agent = Orchestrator()

    agent.start(
        "Find the best KDP book opportunity"
    )


if __name__ == "__main__":
    main()
