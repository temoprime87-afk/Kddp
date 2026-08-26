class ResearchAgent:

    def __init__(self):
        self.name = "Deep Research Agent"

    def run(self, topic):
        return {
            "agent": self.name,
            "topic": topic,
            "status": "ready"
        }
