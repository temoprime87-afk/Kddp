import os
import json
import re
import time
from pathlib import Path

from tavily import TavilyClient
from google import genai


# ============================================================
# KDP AUTONOMOUS BOOK AGENT
# Gemini + Tavily
# Research -> Analysis -> Planning -> Writing -> QA
# ============================================================

OUTPUT_DIR = Path("output")

NUMBER_OF_NICHES = 5
SEARCHES_PER_NICHE = 10

BOOK_LANGUAGE = "English"

# Current Gemini model
MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# ============================================================
# ENVIRONMENT
# ============================================================

def get_required_env(name):

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing {name}. "
            f"Add it to GitHub Actions secrets."
        )

    return value


def get_clients():

    tavily_key = get_required_env(
        "TAVILY_API_KEY"
    )

    gemini_key = get_required_env(
        "GEMINI_API_KEY"
    )

    tavily = TavilyClient(
        api_key=tavily_key
    )

    gemini = genai.Client(
        api_key=gemini_key
    )

    return tavily, gemini


# ============================================================
# FILE HELPERS
# ============================================================

def save_json(filename, data):

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {path}")


def save_text(filename, text):

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)

    print(f"Saved: {path}")


# ============================================================
# TAVILY SEARCH
# ============================================================

def web_search(
    client,
    query,
    max_results=5
):

    print(
        f"\nSEARCH: {query}"
    )

    try:

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True
        )

        results = response.get(
            "results",
            []
        )

        print(
            f"Found {len(results)} sources."
        )

        return {
            "query": query,

            "answer": response.get(
                "answer"
            ),

            "sources": [

                {
                    "title": r.get(
                        "title"
                    ),

                    "url": r.get(
                        "url"
                    ),

                    "content": r.get(
                        "content",
                        ""
                    )[:5000]
                }

                for r in results
            ]
        }

    except Exception as e:

        print(
            f"Search failed: {e}"
        )

        return {
            "query": query,
            "answer": None,
            "sources": [],
            "error": str(e)
        }


# ============================================================
# NICHE DISCOVERY
# ============================================================

def discover_niches(client):

    print("\n" + "=" * 70)

    print(
        "PHASE 1 - NICHE DISCOVERY"
    )

    print("=" * 70)

    queries = [

        "profitable low competition KDP book niches 2026",

        "Amazon Kindle underserved book niches 2026",

        "Amazon paperback niche opportunities 2026",

        "low competition workbook niches 2026",

        "problems people want solved with books"
    ]

    research = []

    for query in queries:

        research.append(
            web_search(
                client,
                query
            )
        )

    candidates = [

        "meal planning for busy families",

        "home organization workbook",

        "beginner hobby workbook",

        "specialized puzzle books",

        "guided self improvement journal"
    ]

    return {
        "queries": research,
        "candidate_niches": candidates
    }


# ============================================================
# NICHE RESEARCH
# ============================================================

def research_niche(
    client,
    niche
):

    print("\n" + "=" * 70)

    print(
        f"PHASE 2 - RESEARCH: {niche}"
    )

    print("=" * 70)

    queries = [

        f"{niche} market demand 2026",

        f"{niche} Amazon Kindle best sellers",

        f"{niche} Amazon paperback best sellers",

        f"{niche} customer problems",

        f"{niche} customer complaints",

        f"{niche} customer needs",

        f"{niche} competing books",

        f"{niche} competing books reviews",

        f"{niche} underserved audience",

        f"{niche} Amazon keywords"
    ]

    results = []

    for query in queries:

        results.append(
            web_search(
                client,
                query
            )
        )

    return results


# ============================================================
# GEMINI TEXT CALL
# ============================================================

def gemini_text(
    client,
    system_prompt,
    user_prompt,
    max_output_tokens=6000
):

    prompt = f"""
SYSTEM INSTRUCTIONS:

{system_prompt}

USER TASK:

{user_prompt}
"""

    max_attempts = 5

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                f"Gemini request "
                f"{attempt}/{max_attempts}"
            )

            response = client.models.generate_content(

                model=MODEL,

                contents=prompt,

                config={
                    "max_output_tokens": max_output_tokens
                }
            )

            text = response.text

            if not text:

                raise RuntimeError(
                    "Gemini returned empty response."
                )

            return text.strip()

        except Exception as e:

            error_text = str(e)

            print(
                f"Gemini error: {error_text}"
            )

            # ------------------------------------------------
            # Do NOT retry model-not-found errors.
            # Retrying a 404 five times only wastes time.
            # ------------------------------------------------

            if (
                "404" in error_text
                or "NOT_FOUND" in error_text
                or "not found" in error_text.lower()
                or "no longer available" in error_text.lower()
            ):

                print(
                    "\nGemini model error detected."
                )

                print(
                    f"Current model: {MODEL}"
                )

                print(
                    "Check GEMINI_MODEL in GitHub Actions."
                )

                raise

            if attempt == max_attempts:

                raise

            wait_seconds = 5 * attempt

            print(
                f"Waiting {wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )


# ============================================================
# GEMINI JSON CALL
# ============================================================

def ask_json(
    client,
    system_prompt,
    user_prompt
):

    text = gemini_text(

        client,

        system_prompt,

        user_prompt,

        max_output_tokens=7000
    )

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # --------------------------------------------------------
    # Try direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(
            text
        )

    except json.JSONDecodeError:

        pass

    # --------------------------------------------------------
    # Try extracting JSON object
    # --------------------------------------------------------

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = text[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:

            pass

    raise RuntimeError(
        "Gemini returned invalid JSON:\n"
        + text[:5000]
    )


# ============================================================
# NICHE ANALYSIS
# ============================================================

def analyze_niche(
    client,
    niche,
    research
):

    print("\n" + "=" * 70)

    print(
        f"PHASE 3 - AI ANALYSIS: {niche}"
    )

    print("=" * 70)

    research_text = json.dumps(
        research,
        ensure_ascii=False
    )

    research_text = research_text[
        :50000
    ]

    system = """

You are an expert Amazon KDP market
research analyst.

Analyze the research evidence carefully.

Never claim guaranteed sales.

Do not invent statistics.

Do not pretend that search results prove
sales unless the evidence actually supports it.

Use scores from 0 to 100.

Evaluate:

- customer demand
- competition
- customer problems
- customer complaints
- underserved needs
- differentiation
- keyword intent
- practical value
- commercial risk

Return ONLY valid JSON.
"""

    user = f"""

NICHE:

{niche}


RESEARCH:

{research_text}


Return exactly this JSON structure:

{{
  "niche": "...",
  "demand_score": 0,
  "competition_score": 0,
  "problem_score": 0,
  "differentiation_score": 0,
  "keyword_score": 0,
  "overall_score": 0,
  "decision": "GO",
  "target_reader": "...",
  "main_problems": [],
  "customer_needs": [],
  "competitor_weaknesses": [],
  "differentiation_strategy": [],
  "book_opportunities": [],
  "risks": []
}}
"""

    return ask_json(
        client,
        system,
        user
    )


# ============================================================
# SELECT BEST NICHE
# ============================================================

def select_best_niche(
    client,
    analyses
):

    print("\n" + "=" * 70)

    print(
        "PHASE 4 - SELECTING BEST NICHE"
    )

    print("=" * 70)

    if not analyses:

        raise RuntimeError(
            "No niche analyses were generated."
        )

    best = max(

        analyses,

        key=lambda x: x.get(
            "overall_score",
            0
        )
    )

    print(
        f"\nBEST NICHE: "
        f"{best['niche']}"
    )

    print(
        f"SCORE: "
        f"{best['overall_score']}/100"
    )

    return best


# ============================================================
# BOOK PLAN
# ============================================================

def create_book_plan(
    client,
    niche_analysis
):

    print("\n" + "=" * 70)

    print(
        "PHASE 5 - BOOK PLAN"
    )

    print("=" * 70)

    analysis_text = json.dumps(
        niche_analysis,
        ensure_ascii=False
    )

    system = """

You are a professional nonfiction
book architect.

Create an original and commercially
sensible KDP book plan.

Do not copy existing books.

Do not imitate a living author's style.

Do not invent statistics.

Return ONLY valid JSON.
"""

    user = f"""

Create a complete book plan from:

{analysis_text}


Return:

{{
  "book_concept": "...",

  "target_reader": "...",

  "title_options": [],

  "subtitle_options": [],

  "unique_value_proposition": "...",

  "table_of_contents": [

    {{
      "chapter": 1,
      "title": "...",
      "purpose": "...",
      "key_points": []
    }}

  ],

  "reader_outcome": "...",

  "keywords": [],

  "categories_ideas": [],

  "content_rules": []
}}


Create 8 to 12 chapters.
"""

    return ask_json(
        client,
        system,
        user
    )


# ============================================================
# CHAPTER WRITING
# ============================================================

def write_chapter(
    client,
    book_plan,
    chapter
):

    title = chapter[
        "title"
    ]

    print(
        f"\nWRITING CHAPTER "
        f"{chapter['chapter']}: {title}"
    )

    system = """

You are a professional nonfiction
ghostwriter.

Write original, useful and practical
content.

Requirements:

- Do not invent statistics.
- Do not copy source text.
- Do not imitate a living author's style.
- Avoid filler.
- Use clear English.
- Use useful examples.
- Make the chapter actionable.
- Stay consistent with the book plan.
- Do not mention that you are an AI.
"""

    user = f"""

BOOK PLAN:

{json.dumps(
    book_plan,
    ensure_ascii=False
)}


CHAPTER:

{json.dumps(
    chapter,
    ensure_ascii=False
)}


Write this chapter.

Use:

- clear headings
- practical explanations
- examples
- actionable steps
- concise summaries

Do not include meta commentary.
"""

    return gemini_text(

        client,

        system,

        user,

        max_output_tokens=10000
    )


# ============================================================
# QUALITY CHECK
# ============================================================

def quality_check(
    client,
    book_plan,
    manuscript
):

    print("\n" + "=" * 70)

    print(
        "PHASE 7 - QUALITY CHECK"
    )

    print("=" * 70)

    manuscript_sample = manuscript[
        :60000
    ]

    system = """

You are a strict editorial
quality-control agent.

Evaluate the manuscript honestly.

Do not say it is perfect.

Do not invent problems that are not
present.

Return ONLY valid JSON.
"""

    user = f"""

BOOK PLAN:

{json.dumps(
    book_plan,
    ensure_ascii=False
)}


MANUSCRIPT:

{manuscript_sample}


Evaluate:

{{
  "overall_quality": 0,
  "originality": 0,
  "usefulness": 0,
  "structure": 0,
  "clarity": 0,
  "filler_risk": 0,
  "issues": [],
  "recommended_fixes": [],
  "ready_for_human_review": true
}}
"""

    return ask_json(
        client,
        system,
        user
    )


# ============================================================
# MARKDOWN MANUSCRIPT
# ============================================================

def build_manuscript(
    book_plan,
    chapters
):

    lines = []

    title_options = book_plan.get(
        "title_options",
        []
    )

    if title_options:

        title = title_options[0]

    else:

        title = "Untitled Book"

    subtitle = ""

    subtitle_options = book_plan.get(
        "subtitle_options",
        []
    )

    if subtitle_options:

        subtitle = subtitle_options[0]

    lines.append(
        f"# {title}"
    )

    lines.append("")

    if subtitle:

        lines.append(
            f"## {subtitle}"
        )

        lines.append("")

    lines.append(
        f"**Book concept:** "
        f"{book_plan.get('book_concept', '')}"
    )

    lines.append("")

    lines.append("---")

    lines.append("")

    for chapter in chapters:

        lines.append(

            f"# Chapter "
            f"{chapter['chapter']}: "
            f"{chapter['title']}"

        )

        lines.append("")

        lines.append(
            chapter["content"]
        )

        lines.append("")

        lines.append("---")

        lines.append("")

    return "\n".join(
        lines
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "KDP AUTONOMOUS BOOK AGENT"
    )

    print(
        "Gemini + Tavily"
    )

    print(
        f"Model: {MODEL}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    tavily, gemini = get_clients()

    # --------------------------------------------------------
    # 1. DISCOVER NICHES
    # --------------------------------------------------------

    discovery = discover_niches(
        tavily
    )

    save_json(
        "01_niche_discovery.json",
        discovery
    )

    niches = discovery[
        "candidate_niches"
    ][:NUMBER_OF_NICHES]

    # --------------------------------------------------------
    # 2. RESEARCH + ANALYZE NICHES
    # --------------------------------------------------------

    niche_analyses = []

    for index, niche in enumerate(
        niches,
        start=1
    ):

        research = research_niche(
            tavily,
            niche
        )

        save_json(

            f"research_{index}.json",

            {
                "niche": niche,
                "research": research
            }
        )

        analysis = analyze_niche(

            gemini,

            niche,

            research
        )

        niche_analyses.append(
            analysis
        )

        time.sleep(2)

    save_json(
        "02_niche_analyses.json",
        niche_analyses
    )

    # --------------------------------------------------------
    # 3. SELECT WINNER
    # --------------------------------------------------------

    winner = select_best_niche(
        gemini,
        niche_analyses
    )

    save_json(
        "03_selected_niche.json",
        winner
    )

    # --------------------------------------------------------
    # 4. CREATE BOOK PLAN
    # --------------------------------------------------------

    book_plan = create_book_plan(
        gemini,
        winner
    )

    save_json(
        "04_book_plan.json",
        book_plan
    )

    # --------------------------------------------------------
    # 5. WRITE BOOK
    # --------------------------------------------------------

    chapters = []

    table_of_contents = book_plan.get(
        "table_of_contents",
        []
    )

    if not table_of_contents:

        raise RuntimeError(
            "Gemini did not create a table of contents."
        )

    for chapter in table_of_contents:

        content = write_chapter(

            gemini,

            book_plan,

            chapter
        )

        chapters.append(

            {
                **chapter,
                "content": content
            }
        )

        time.sleep(2)

    # --------------------------------------------------------
    # 6. BUILD MANUSCRIPT
    # --------------------------------------------------------

    manuscript = build_manuscript(

        book_plan,

        chapters
    )

    save_text(
        "05_manuscript.md",
        manuscript
    )

    save_json(
        "05_chapters.json",
        chapters
    )

    # --------------------------------------------------------
    # 7. QUALITY CHECK
    # --------------------------------------------------------

    qa = quality_check(

        gemini,

        book_plan,

        manuscript
    )

    save_json(
        "06_quality_check.json",
        qa
    )

    # --------------------------------------------------------
    # 8. FINAL REPORT
    # --------------------------------------------------------

    final_report = {

        "agent":
            "KDP Autonomous Book Agent",

        "ai_model":
            MODEL,

        "selected_niche":
            winner,

        "book_plan":
            book_plan,

        "quality_check":
            qa,

        "status":
            (
                "READY_FOR_HUMAN_REVIEW"

                if qa.get(
                    "ready_for_human_review",
                    False
                )

                else "NEEDS_REVIEW"
            )
    }

    save_json(
        "07_final_report.json",
        final_report
    )

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------

    print("\n")

    print("=" * 70)

    print(
        "AGENT FINISHED"
    )

    print("=" * 70)

    print(
        f"\nSelected niche: "
        f"{winner.get('niche', 'Unknown')}"
    )

    print(
        f"Opportunity score: "
        f"{winner.get('overall_score', 0)}/100"
    )

    print(
        f"Quality score: "
        f"{qa.get('overall_quality', 0)}/100"
    )

    print(
        "\nAll results are inside "
        "the output/ folder."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
