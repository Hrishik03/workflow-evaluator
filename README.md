# AI Workflow Evaluator

This project is a Streamlit app that evaluates how effectively an engineer uses AI during software development conversations.

It accepts transcript files (`.txt`, `.md`, `.pdf`, `.doc`, `.docx`), parses user/AI turns, sends them to Groq for scoring, and displays:

- Prompt Clarity
- Iteration Quality
- Debugging Approach
- AI Utilization
- Overall Score (weighted)
- Confidence Score (%)
- Detected development phases and phase distribution
- Strengths, improvements, and summary

## Project Structure

- `app.py` - Streamlit UI, file upload, multi-transcript evaluation, charts, and summary table
- `analyzer.py` - transcript parsing + Groq-based scoring + phase detection + confidence scoring
- `requirements.txt` - Python dependencies

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Run the App

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## How to Use

1. Upload one or more transcript files.
2. Click **Analyze all uploaded transcripts**.
3. Review:
   - top summary table (when multiple files are uploaded)
   - per-transcript metrics and charts
   - phase analysis
   - JSON output per transcript

## Transcript Formatting Notes

For best parsing results, use speaker labels such as:

- `User: ...`
- `Assistant: ...`
- `AI: ...`
- `Human: ...`

Markdown-style speaker formats are also supported (for example `## User`, `**Assistant:** ...`).
