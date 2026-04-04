# AI Workflow Evaluator

A Streamlit app that evaluates how effectively an engineer uses AI during software development conversations.

It accepts transcript files (`.txt`, `.md`, `.pdf`, `.doc`, `.docx`), parses user/AI turns, sends them to Groq for scoring, and displays structured insights across multiple dimensions.

## What It Evaluates

- **Prompt Clarity** — how specific and well-defined the prompts were
- **Iteration Quality** — whether the engineer refined prompts vs accepting first responses
- **Debugging Approach** — how effectively AI was used to identify and fix issues
- **AI Utilization** — whether AI was used for the right tasks at the right time
- **Overall Score** — weighted average across all metrics
- **Confidence Score** — combined model confidence + signal quality factor
- **Phase Detection** — identifies development phases (planning, implementation, debugging, etc.)
- **Strengths & Improvements** — concrete, actionable feedback per session

## Project structure

| File | Purpose |
|------|---------|
| [`app.py`](app.py) | Streamlit app: uploads, per-file analysis, charts, multi-file summary |
| [`analyzer.py`](analyzer.py) | Parse transcripts → Groq evaluation → metrics, phases, confidence |
| [`requirements.txt`](requirements.txt) | Python dependencies |
| [`.gitignore`](.gitignore) | Ignores `.env`, venvs, caches, etc. |
| `README.md` | This documentation |

Local-only (create yourself, not in the repo): `.env` with `GROQ_API_KEY`.

Optional: a `transcripts/` folder for sample or test uploads — not required to run the app.

## Approach

Transcripts are parsed into structured user/assistant turns using regex-based pattern matching that supports multiple formats (plain text, markdown headings, bold labels). The parsed turns are sent to Groq (LLaMA 3) with a structured prompt that instructs the model to return strict JSON scores.

A **signal quality factor** is computed locally based on:
- Number of turns in the conversation
- Total character length
- Balance between user and assistant turns

This is combined with the **model's self-reported confidence** to produce a final confidence score, giving a more reliable picture of how trustworthy the evaluation is for short or sparse transcripts.

When multiple transcripts are uploaded, a **comparison table** is shown at the top summarizing scores across all sessions.

## What Makes a Good AI Workflow?

- **Clear, specific prompts** with enough context for the AI to give useful responses
- **Iterative refinement** — following up, pushing back, and improving on first responses
- **Structured debugging** — using AI as a thinking partner, not just a answer machine
- **Appropriate utilization** — knowing when to use AI and when to think independently
- **Phase awareness** — moving deliberately through planning, implementation, and testing

## Setup

**Requirements:** Python 3.9+

1. Clone the repository and navigate into it.

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

You can get a free Groq API key at [console.groq.com](https://console.groq.com).

## Run the App
```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## How to Use

1. Upload one or more transcript files
2. Click **Analyze all uploaded transcripts**
3. Review:
   - Summary comparison table (when multiple files uploaded)
   - Per-transcript metric scores and bar charts
   - Phase detection and distribution
   - Strengths, improvements, and summary per session

## Transcript Format

For best results, use speaker labels like:

- `User: ...` / `Human: ...`
- `Assistant: ...` / `AI: ...`

Markdown-style formats are also supported:

- `## User` followed by content on the next line
- `**User**` / `**Cursor**` on their own lines (Cursor export)
- `**Assistant:** ...`
- `> User: ...`

## Sample transcripts

The `transcripts/` folder contains real anonymized coding sessions used during development and testing, sourced from Cursor and Claude sessions.