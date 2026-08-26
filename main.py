import json
import os
import re
from datetime import datetime


# ============================================================
# KDP AUTONOMOUS RESEARCH ENGINE
# Version 1.0
# ============================================================


def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def score_demand(demand):
    """Convert demand level to a numerical score."""
    values = {
        "very_high": 95,
        "high": 80,
        "medium": 60,
        "low": 35,
        "very_low": 15,
    }

    return values.get(str(demand).lower(), 50)


def score_competition(competition):
    """Lower competition is better."""
    values = {
        "very_low": 95,
        "low": 80,
        "medium": 60,
        "high": 35,
        "very_high": 15,
    }

    return values.get(str(competition).lower(), 50)


def score_profitability(profitability):
    """Convert profitability level to score."""
    values = {
        "very_high": 95,
        "high": 80,
        "medium": 60,
        "low": 35,
        "very_low": 15,
    }

    return values.get(str(profitability).lower(), 50)


def calculate_opportunity_score(
    demand,
    competition,
    profitability,
    differentiation,
):
    """
    Main opportunity score.

    Demand:
        30%

    Competition:
        30%

    Profitability:
        20%

    Differentiation:
        20%
    """

    final_score = (
        demand * 0.30
        + competition * 0.30
        + profitability * 0.20
        + differentiation * 0.20
    )

    return round(final_score, 2)


def create_niche(
    name,
    audience,
    demand,
    competition,
    profitability,
    differentiation,
    problems,
    book_angles,
):
    """Create a structured niche object."""

    demand_score = score_demand(demand)
    competition_score = score_competition(competition)
    profitability_score = score_profitability(profitability)

    opportunity_score = calculate_opportunity_score(
        demand_score,
        competition_score,
        profitability_score,
        differentiation,
    )

    return {
        "niche": clean_text(name),
        "target_audience": clean_text(audience),
        "demand": demand,
        "demand_score": demand_score,
        "competition": competition,
        "competition_score": competition_score,
        "profitability": profitability,
        "profitability_score": profitability_score,
        "differentiation_score": differentiation,
        "opportunity_score": opportunity_score,
        "problems": problems,
        "book_angles": book_angles,
    }


def generate_initial_market_map():
    """
    Initial research map.

    This is NOT the final research.
    It gives the agent a structured starting point.
    """

    niches = [

        create_niche(
            name="Practical Journaling",
            audience="Adults interested in productivity and self-reflection",
            demand="high",
            competition="high",
            profitability="medium",
            differentiation=72,
            problems=[
                "Difficulty maintaining a journaling habit",
                "Lack of structured prompts",
                "Overcomplicated journaling systems",
            ],
            book_angles=[
                "30-day guided journal",
                "Minimalist daily journal",
                "Problem-solving journal",
            ],
        ),

        create_niche(
            name="Meal Planning for Busy People",
            audience="Busy adults and families",
            demand="high",
            competition="high",
            profitability="high",
            differentiation=75,
            problems=[
                "Lack of time",
                "Difficulty deciding what to cook",
                "Food waste",
                "Poor weekly organization",
            ],
            book_angles=[
                "30-day meal planner",
                "Simple weekly meal system",
                "Budget meal planning workbook",
            ],
        ),

        create_niche(
            name="Home Organization",
            audience="People trying to simplify and organize their homes",
            demand="high",
            competition="high",
            profitability="medium",
            differentiation=78,
            problems=[
                "Clutter",
                "Lack of organization systems",
                "Difficulty maintaining routines",
            ],
            book_angles=[
                "30-day decluttering challenge",
                "Room-by-room organization workbook",
                "Minimalist home planner",
            ],
        ),

        create_niche(
            name="Beginner Hobby Workbooks",
            audience="Adults starting new hobbies",
            demand="medium",
            competition="medium",
            profitability="medium",
            differentiation=85,
            problems=[
                "Beginners don't know where to start",
                "Lack of structured practice",
                "Difficulty tracking progress",
            ],
            book_angles=[
                "30-day beginner challenge",
                "Progress tracker workbook",
                "Practice journal",
            ],
        ),

        create_niche(
            name="Specialized Puzzle Books",
            audience="Adults who enjoy puzzles and brain games",
            demand="high",
            competition="high",
            profitability="high",
            differentiation=82,
            problems=[
                "Generic puzzle books are repetitive",
                "Readers want specialized themes",
                "Need for varied difficulty",
            ],
            book_angles=[
                "Themed puzzle collection",
                "Progressive difficulty puzzle book",
                "Large-print puzzle workbook",
            ],
        ),

    ]

    return niches


def rank_niches(niches):
    """Rank niches from strongest to weakest opportunity."""

    return sorted(
        niches,
        key=lambda item: item["opportunity_score"],
        reverse=True,
    )


def generate_research_report(niches):
    """Generate the final research report."""

    ranked = rank_niches(niches)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_niches_analyzed": len(ranked),
        "ranked_niches": ranked,
        "top_opportunity": ranked[0] if ranked else None,
    }

    return report


def save_report(report):
    """Save research results as JSON."""

    output_file = "kdp_research_report.json"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_file


def print_final_result(report):
    """Display the final result in GitHub Actions logs."""

    print("")
    print("=" * 65)
    print("KDP AUTONOMOUS RESEARCH ENGINE")
    print("=" * 65)
    print("")

    print(
        f"Niches analyzed: "
        f"{report['total_niches_analyzed']}"
    )

    print("")

    print("TOP OPPORTUNITY")
    print("-" * 65)

    top = report["top_opportunity"]

    if not top:
        print("No opportunity found.")
        return

    print(
        f"Niche: {top['niche']}"
    )

    print(
        f"Target audience: "
        f"{top['target_audience']}"
    )

    print(
        f"Demand score: "
        f"{top['demand_score']}/100"
    )

    print(
        f"Competition score: "
        f"{top['competition_score']}/100"
    )

    print(
        f"Profitability score: "
        f"{top['profitability_score']}/100"
    )

    print(
        f"Differentiation score: "
        f"{top['differentiation_score']}/100"
    )

    print(
        f"OPPORTUNITY SCORE: "
        f"{top['opportunity_score']}/100"
    )

    print("")

    print("Potential book angles:")

    for angle in top["book_angles"]:
        print(f"  - {angle}")

    print("")
    print("=" * 65)
    print("Research report saved to kdp_research_report.json")
    print("=" * 65)
    print("")


def main():
    print("")
    print("=" * 65)
    print("KDP AUTONOMOUS AGENT")
    print("=" * 65)
    print("")

    print("Starting research engine...")
    print("")

    niches = generate_initial_market_map()

    print(
        f"Analyzing {len(niches)} initial opportunities..."
    )

    report = generate_research_report(niches)

    output_file = save_report(report)

    print_final_result(report)

    print(
        f"Saved: {output_file}"
    )


if __name__ == "__main__":
    main()
