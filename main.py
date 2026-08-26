import json
import os
import re
from datetime import datetime, timezone

import requests


TAVILY_URL = "https://api.tavily.com/search"


# ============================================================
# KDP WEB RESEARCH ENGINE
# ============================================================


def clean_text(value):
    if value is None:
        return ""

    value = str(value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def get_api_key():
    key = os.getenv("TAVILY_API_KEY", "").strip()

    if not key:
        raise RuntimeError(
            "Missing TAVILY_API_KEY. "
            "Add it to GitHub Actions secrets."
        )

    return key


def search_web(query, api_key, max_results=5):
    """
    Search the web using Tavily.
    """

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": False,
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def extract_results(search_response):
    results = []

    for item in search_response.get("results", []):
        results.append(
            {
                "title": clean_text(item.get("title")),
                "url": clean_text(item.get("url")),
                "content": clean_text(item.get("content")),
                "score": item.get("score"),
            }
        )

    return results


def research_niche(niche, api_key):
    """
    Perform multiple searches around one niche.
    """

    queries = [
        f"{niche} market demand trends",
        f"{niche} problems customers want solved",
        f"{niche} books Amazon Kindle paperback bestseller",
        f"{niche} competitors books reviews",
        f"{niche} underserved audience opportunities",
    ]

    research = {
        "niche": niche,
        "queries": [],
        "sources": [],
    }

    for query in queries:

        print("")
        print(f"SEARCH: {query}")

        try:
            response = search_web(
                query,
                api_key,
                max_results=5,
            )

            results = extract_results(response)

            research["queries"].append(
                {
                    "query": query,
                    "answer": clean_text(
                        response.get("answer", "")
                    ),
                    "results": results,
                }
            )

            for result in results:
                research["sources"].append(result)

            print(
                f"Found {len(results)} sources."
            )

        except Exception as error:

            print(
                f"Search failed: {error}"
            )

            research["queries"].append(
                {
                    "query": query,
                    "error": str(error),
                    "results": [],
                }
            )

    return research


def calculate_basic_score(research):
    """
    Preliminary score based on research coverage.

    This is NOT a sales guarantee.
    """

    source_count = len(
        research.get("sources", [])
    )

    unique_domains = set()

    for source in research.get("sources", []):

        url = source.get("url", "")

        match = re.search(
            r"https?://([^/]+)",
            url,
        )

        if match:
            unique_domains.add(
                match.group(1).lower()
            )

    source_score = min(
        source_count * 5,
        50,
    )

    diversity_score = min(
        len(unique_domains) * 5,
        30,
    )

    coverage_score = min(
        len(research.get("queries", [])) * 4,
        20,
    )

    score = (
        source_score
        + diversity_score
        + coverage_score
    )

    return min(round(score, 2), 100)


def save_json(filename, data):
    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():

    print("")
    print("=" * 70)
    print("KDP AUTONOMOUS WEB RESEARCH ENGINE")
    print("=" * 70)
    print("")

    api_key = get_api_key()

    # Initial research targets.
    # Later the agent will discover these automatically.
    niches = [
        "meal planning for busy families",
        "home organization workbook",
        "beginner hobby workbook",
        "specialized puzzle books",
        "guided self improvement journal",
    ]

    all_research = []

    for number, niche in enumerate(
        niches,
        start=1,
    ):

        print("")
        print("=" * 70)
        print(
            f"NICHE {number}/{len(niches)}: {niche}"
        )
        print("=" * 70)

        research = research_niche(
            niche,
            api_key,
        )

        score = calculate_basic_score(
            research
        )

        research["preliminary_research_score"] = score

        all_research.append(research)

        print("")
        print(
            f"Preliminary research score: "
            f"{score}/100"
        )

    all_research.sort(
        key=lambda item: item.get(
            "preliminary_research_score",
            0,
        ),
        reverse=True,
    )

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "engine": (
            "KDP Autonomous Web Research Engine"
        ),

        "important_note": (
            "Research scores are analytical signals, "
            "not guarantees of sales."
        ),

        "niches_analyzed": len(
            all_research
        ),

        "ranking": all_research,
    }

    save_json(
        "kdp_web_research.json",
        report,
    )

    print("")
    print("=" * 70)
    print("FINAL RESEARCH RESULT")
    print("=" * 70)

    if all_research:

        winner = all_research[0]

        print("")
        print(
            f"TOP RESEARCH OPPORTUNITY: "
            f"{winner['niche']}"
        )

        print(
            f"SCORE: "
            f"{winner['preliminary_research_score']}/100"
        )

        print(
            f"SOURCES: "
            f"{len(winner.get('sources', []))}"
        )

    print("")
    print(
        "Saved: kdp_web_research.json"
    )

    print("")
    print("=" * 70)


if __name__ == "__main__":
    main()
