from agents.research_agent import ResearchAgent


class Orchestrator:

    def __init__(self):
        self.research_agent = ResearchAgent()

    def start(self, topic):
        print("Starting KDP Agent...")
        print("Running deep research...")

        result = self.research_agent.run(topic)

        print("Research completed.")
        print(result)

        return result


if __name__ == "__main__":
    agent = Orchestrator()

    agent.start(
        "Find profitable KDP book opportunities"
    )
