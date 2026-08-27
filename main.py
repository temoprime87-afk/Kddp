import os
import json
from tavily import TavilyClient


# ============================================================
# KDP AUTONOMOUS RESEARCH AGENT v2
# ============================================================

def get_api_key():
    key = os.getenv("TAVILY_API_KEY")

    if not key:
        raise RuntimeError(
            "Missing TAVILY_API_KEY. "
            "Add it to GitHub Actions secrets."
        )

    return key


def search(client, query, max_results=5):
    print(f"\nSEARCH: {query}")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True
        )

        results = response.get("results", [])

        print(f"Found {len(results)} sources.")

        return {
            "query": query,
            "answer": response.get("answer"),
            "sources": [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content", "")[:3000]
                }
                for item in results
            ]
        }

    except Exception as e:
        print(f"Search error: {e}")

        return {
            "query": query,
            "answer": None,
            "sources": [],
            "error": str(e)
        }


def deep_research(client, niche):
    print("\n" + "=" * 60)
    print(f"DEEP RESEARCH: {niche}")
    print("=" * 60)

    queries = [
        f"{niche} market demand trends",
        f"{niche} Amazon Kindle books best sellers",
        f"{niche} Amazon paperback books reviews",
        f"{niche} customer problems complaints",
        f"{niche} customer needs underserved audience",
        f"{niche} competing books weaknesses",
        f"{niche} book keywords Amazon",
        f"{niche} profitable book ideas",
        f"{niche} low competition keywords",
        f"{niche} book ideas 2026"
    ]

    research = []

    for query in queries:
        result = search(client, query)
        research.append(result)

    return research


def analyze_research(niche, research):
    all_sources = []

    for item in research:
        for source in item.get("sources", []):
            all_sources.append(source)

    unique_urls = set()

    unique_sources = []

    for source in all_sources:
        url = source.get("url")

        if url and url not in unique_urls:
            unique_urls.add(url)
            unique_sources.append(source)

    # Simple evidence-based scoring.
    # This is NOT a guarantee of sales.
    source_count = len(unique_sources)

    demand_score = min(100, 50 + source_count * 2)
    competition_score = min(100, 50 + source_count)
    opportunity_score = round(
        (demand_score + (100 - competition_score)) / 2
    )

    if opportunity_score >= 70:
        decision = "GO"
    elif opportunity_score >= 50:
        decision = "REVIEW"
    else:
        decision = "NO-GO"

    return {
        "niche": niche,
        "decision": decision,
        "scores": {
            "research_depth": min(100, source_count * 4),
            "demand_signal": demand_score,
            "competition_signal": competition_score,
            "opportunity_score": opportunity_score
        },
        "source_count": source_count,
        "sources": unique_sources
    }


def save_report(report):
    with open(
        "kdp_deep_research_report.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nSaved: kdp_deep_research_report.json")


def main():
    print("=" * 60)
    print("KDP AUTONOMOUS RESEARCH ENGINE v2")
    print("=" * 60)

    client = TavilyClient(api_key=get_api_key())

    # Niche selected by the previous research stage.
    niche = "meal planning for busy families"

    research = deep_research(
        client,
        niche
    )

    analysis = analyze_research(
        niche,
        research
    )

    report = {
        "agent": "KDP Autonomous Research Agent v2",
        "niche": niche,
        "research_queries": len(research),
        "analysis": analysis
    }

    print("\n" + "=" * 60)
    print("FINAL DEEP RESEARCH RESULT")
    print("=" * 60)

    print(f"\nNICHE: {niche}")
    print(f"DECISION: {analysis['decision']}")
    print(
        f"OPPORTUNITY SCORE: "
        f"{analysis['scores']['opportunity_score']}/100"
    )
    print(
        f"UNIQUE SOURCES: "
        f"{analysis['source_count']}"
    )

    save_report(report)


if __name__ == "__main__":
    main()
