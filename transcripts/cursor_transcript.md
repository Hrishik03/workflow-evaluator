# Transcript parsing and evaluation script
_Exported on 4/3/2026 at 23:32:34 GMT+5:30 from Cursor (2.6.22)_

---

**User**

in @analyzer.py i want a python script to:
Parse the transcript — break it into user messages vs AI responses
Evaluate — send it to Groq and get quality scores
Return structured results that app.py can display

---

**Cursor**

I’ll implement `analyzer.py` end-to-end so it parses transcript turns, calls Groq for evaluation, and returns structured output for `app.py`. I’m first checking the current files to align function names and expected data flow.

I found both `analyzer.py` and `app.py` empty, so I’ll build `analyzer.py` as a reusable module with clear functions (`parse`, `evaluate`, `analyze`) and a stable response schema that `app.py` can consume directly.

Implemented `analyzer.py` with a full pipeline that `app.py` can call directly.

### What it now does

- **Parses transcript into turns** via `parse_transcript(transcript)`
  - Supports prefixes like `user:`, `human:`, `assistant:`, `ai:`
  - Normalizes roles to `user` and `assistant`
  - Handles multi-line messages

- **Evaluates quality with Groq** via `evaluate_transcript_with_groq(turns, model, api_key)`
  - Uses `GROQ_API_KEY` from env (or passed `api_key`)
  - Sends a strict JSON scoring prompt
  - Returns stable metric structure
  - Includes safe fallback handling for missing key / malformed model output

- **Returns structured result for UI** via `analyze_transcript(transcript, model, api_key)`
  - Includes message counts
  - Includes parsed turns
  - Includes evaluation object

### Output shape from `analyze_transcript(...)`

```python
{
  "counts": {
    "total_turns": int,
    "user_messages": int,
    "ai_messages": int
  },
  "turns": [
    {"role": "user" | "assistant", "content": "..."}
  ],
  "evaluation": {
    "overall_score": number,
    "metrics": {
      "relevance": number,
      "accuracy": number,
      "clarity": number,
      "helpfulness": number
    },
    "strengths": [str, ...],
    "improvements": [str, ...],
    "summary": str,
    # optional "error" if applicable
  }
}
```

If you want, I can next scaffold `app.py` to call `analyze_transcript()` and render these results in Streamlit.

---

**User**

the metrics should be based on:

Prompt Clarity — were the prompts specific and well-defined?
Iteration Quality — did the engineer refine/follow up or just accept first answer?
Debugging Approach — how well did they handle errors/problems?
AI Utilization — did they use AI for the right things?
Overall Score — weighted average of all

are the current now meeting them

---

**Cursor**

I’ll quickly inspect `analyzer.py` against your metric definitions and map exactly what’s aligned vs missing.

Short answer: **not yet**.

Your current evaluator is using these metrics instead:

- `relevance`
- `accuracy`
- `clarity`
- `helpfulness`

This is defined in the prompt and schema here:

```63:80:c:\Users\HRISHIKESH\Desktop\Web development\workflow_eval\analyzer.py
def _build_eval_prompt(turns: List[Dict[str, str]]) -> str:
    ...
        '  "metrics": {\n'
        '    "relevance": <number 1-10>,\n'
        '    "accuracy": <number 1-10>,\n'
        '    "clarity": <number 1-10>,\n'
        '    "helpfulness": <number 1-10>\n'
```

And the returned normalization also expects those keys:

```180:188:c:\Users\HRISHIKESH\Desktop\Web development\workflow_eval\analyzer.py
    return {
        "overall_score": parsed.get("overall_score", 0),
        "metrics": {
            "relevance": parsed.get("metrics", {}).get("relevance", 0),
            "accuracy": parsed.get("metrics", {}).get("accuracy", 0),
            "clarity": parsed.get("metrics", {}).get("clarity", 0),
            "helpfulness": parsed.get("metrics", {}).get("helpfulness", 0),
```

So against your required framework, the gaps are:

- **Prompt Clarity**: not explicitly scored as your definition
- **Iteration Quality**: missing
- **Debugging Approach**: missing
- **AI Utilization**: missing
- **Overall Score as weighted average**: currently model-provided directly, not computed by your own weighting logic

If you want, I can give you the exact replacement schema + weighted formula logic (e.g., 25/25/25/25 or custom weights) so you can update `analyzer.py` in one pass when you switch back to Agent mode.

---

**User**

make that changes also i want the final json result in this format:

{
  "prompt_clarity": 8,
  "iteration_quality": 7,
  "debugging_approach": 6,
  "ai_utilization": 8,
  "overall_score": 7.5,
  "summary": "...",
  "strengths": [...],
  "improvements": [...]
}

---

**Cursor**

Got it. I’ll update `analyzer.py` so Groq scores the four required dimensions, then **compute `overall_score` as a weighted average**, and finally return **exactly** the JSON shape you specified. I’ll keep the parser as-is and adjust the evaluation prompt + normalization.

Now `analyzer.analyze_transcript()` returns *exactly* your requested JSON shape, with `overall_score` computed as a weighted average of the four metrics (defaults to equal weights). Next I’ll run a quick lint check to ensure the refactor didn’t introduce issues.

### Updated behavior (meets your metric definitions)

`analyzer.py` now evaluates and returns this **final JSON format**:

```json
{
  "prompt_clarity": 8,
  "iteration_quality": 7,
  "debugging_approach": 6,
  "ai_utilization": 8,
  "overall_score": 7.5,
  "summary": "...",
  "strengths": [...],
  "improvements": [...]
}
```

- **Prompt Clarity**: explicitly requested + returned as `prompt_clarity`
- **Iteration Quality**: explicitly requested + returned as `iteration_quality`
- **Debugging Approach**: explicitly requested + returned as `debugging_approach`
- **AI Utilization**: explicitly requested + returned as `ai_utilization`
- **Overall Score**: **computed in code** as a weighted average (defaults to 0.25 each; configurable via `weights=`)

### Note on the warnings you see
The two lints are **environment warnings** (Pyright can’t resolve `dotenv` / `groq`), not code issues. They’ll go away once dependencies are installed in the active interpreter (from your `requirements.txt`: `python-dotenv`, `groq`).

---

**User**

the analyzer's main goal should be “How effectively is this engineer using AI during software development?” so it the entire codebase serving that purpose

---

**Cursor**

I’ll quickly review the current files against that goal and tell you plainly whether the codebase is fully aligned or not.

Mostly **yes at analyzer level**, but **not as an entire codebase yet**.

- `analyzer.py` is now aligned to that goal: it explicitly scores AI-usage-focused dimensions (`prompt_clarity`, `iteration_quality`, `debugging_approach`, `ai_utilization`) and computes weighted `overall_score`.
- The evaluation prompt in `_build_eval_prompt()` is oriented to conversation-quality/AI-use behavior, which fits your main objective.
- `analyze_transcript()` returns the final flattened JSON format you asked for, so downstream UI can display it directly.

What’s missing for “entire codebase” alignment:

- `app.py` is currently empty, so there’s no interface/workflow yet to ensure this goal is enforced end-to-end.
- No tests/validation to confirm scoring behavior is stable and consistent with your rubric.
- No rubric guardrails beyond prompt text (e.g., hard validation of score ranges, required evidence per metric).

So the right verdict is: **core analyzer logic is serving the purpose, but the full project is not complete yet because the app and verification layer are still absent.**

---

**User**

now in the app.py initialize the streamlit app, where it takes the transcripts as pdf,txt,doc & gives the metric result

---

**Cursor**

I’ll build `app.py` as a Streamlit UI with file upload support for `pdf`, `txt`, and `doc` (plus `docx`), extract transcript text, run `analyze_transcript`, and render the metric outputs cleanly. I’ll also add the required parser dependencies.

I’ve wired the upload + scoring flow. I’m doing a quick lint pass now to catch any immediate issues before you run it.

Implemented `app.py` as a working Streamlit app that:

- uploads transcript files: `pdf`, `txt`, `doc`, `docx`
- extracts text by file type
- calls `analyze_transcript(transcript)`
- displays all requested metrics and the final JSON

### What I changed

- Updated `app.py` to include:
  - `extract_text_from_file(...)` for parsing:
    - `.txt` via decode
    - `.pdf` via `pypdf`
    - `.docx` via `python-docx`
    - `.doc` via optional `textract` path
  - Streamlit UI with uploader + metrics cards
  - summary, strengths, improvements display
  - raw JSON viewer (`st.json`)

- Updated `requirements.txt` with:
  - `pypdf`
  - `python-docx`
  - `textract`

### Note

Linter warnings currently show unresolved imports for installed libs (`streamlit`, `docx`, `pypdf`, `textract`) because dependencies are not yet installed in the active environment.

Run:

- `pip install -r requirements.txt`
- `streamlit run app.py`

If you want, I can next add a small “sample transcript format” helper section in the app so users upload cleaner transcripts for more accurate scoring.

---

**User**

currently it only taking pdf,doc,txt file i want it to also take in .md files as well

---

**Cursor**

I’ll add `.md` support in the uploader and text extraction logic (same handling as text files), then quickly lint-check `app.py`.

Done — `.md` is now supported.

Updated in `app.py`:

- File uploader types now include `md`
- Extraction treats `.md` the same as `.txt` (UTF-8 fallback to latin-1)
- Error/help text updated to list `MD` support

No logic changes beyond that.  
The remaining linter warnings are still just unresolved dependency environment warnings.

---

**User**

after uploading the md file, the metrics aint showing up & throws up error of No valid transcript turns were parsed.

---

**Cursor**

I see the issue: your parser currently only recognizes strict `user:` / `assistant:` line prefixes, so many markdown transcript styles won’t parse. I’ll make the parser markdown-tolerant (headings, bold labels, and separator styles) so uploaded `.md` files reliably produce turns.

You were right — parser was too strict for markdown transcripts.

I updated `parse_transcript()` in `analyzer.py` to handle common `.md` chat formats, including:

- `user: ...` / `assistant: ...`
- `**User:** ...` / `**Assistant:** ...`
- `## User` then multiline content
- `## Assistant` then multiline content
- quoted/bulleted forms like `> Assistant: ...`
- aliases like `human`, `ai`, `chatgpt`, `model`

So `.md` files with these patterns should now parse into turns and show metrics instead of `No valid transcript turns were parsed`.

If it still fails on your specific file, paste a small sample of the markdown transcript format here and I’ll tune the parser pattern exactly to that structure.

---

**User**

currently, when i upload a transcript the analysis begin right away, i wan to upload one or more than one transcripts & have a button, which upon clicked starts the analysis ie the result given will consider all the transcript uploaded

---

**Cursor**

I’ll modify `app.py` so it supports **multiple transcript uploads** and only starts Groq analysis when the user clicks a button. I’ll then ensure the final evaluation is computed over the **combined text from all uploaded files**.

I’ll update `app.py` to delay Groq analysis until the user clicks a new `Analyze` button, and to support `accept_multiple_files=True` so the final evaluation runs on the combined text from all uploaded transcripts.

Updated `app.py` to support **uploading one or more transcripts** and to **start analysis only after you click a button**.

### What changed in `app.py`
- `st.file_uploader(...)` now uses `accept_multiple_files=True`
- Added an `Analyze all uploaded transcripts` button
- The app **extracts text immediately**, but **does not call** `analyze_transcript()` until the button is clicked
- When clicked, it combines all extracted texts with `"\n\n".join(...)` and runs **one single evaluation** on the combined transcript

So the resulting metrics will reflect **all uploaded transcripts together**.

If you want, I can also adjust it to show per-file extracted text stats (word/char counts) before analysis.

---

**User**

right now you're combining all transcripts into one with "\n\n".join(extracted_texts) and analyzing as a single blob, however the end goal is to get each transcript evaluated separately

---

**Cursor**

Makes sense — I’ll change the flow to evaluate each uploaded transcript independently and then render results per file (instead of merging into one blob).

Perfect callout — I changed it to evaluate **each transcript separately** now.

### What changed in `app.py`
- Removed combined blob analysis (`"\n\n".join(...)`).
- Keeps uploaded files as:
  - `{"file_name": ..., "transcript": ...}`
- On button click, runs:
  - `analyze_transcript(...)` **once per file**
- Displays results per transcript in separate expanders (`1. filename`, `2. filename`, etc.), each with:
  - 5 metrics
  - summary
  - strengths
  - improvements
  - raw JSON for that file

So now the analysis output is **per transcript**, not a single merged evaluation.

If you want next, I can add a downloadable JSON export containing all file-wise results in one list.

---

**User**

@c:\Users\HRISHIKESH\.cursor\projects\c-Users-HRISHIKESH-Desktop-Web-development-workflow-eval\terminals\4.txt:22-57 got an throw back error

---

**Cursor**

Thanks for sharing the traceback — this is clear: Streamlit doesn’t allow an `st.expander` inside another `st.expander`. I’ll patch `app.py` to remove the nested expander and keep raw JSON visible safely.

You hit a valid Streamlit constraint: **nested expanders are not allowed**.

I fixed `app.py` by removing the inner:

- `with st.expander("Raw JSON result")`

and replacing it with:

- `st.markdown("**Raw JSON result**")`
- `st.json(result)`

inside each file’s outer expander.

This resolves the traceback from your terminal log.  
Rerun/refresh the app and it should render normally now.

---

**User**

phase detection is still not implemented in @analyzer.py isn't?

---

**Cursor**

Correct — **phase detection is not implemented yet** in `analyzer.py`.

Right now it does:

- transcript parsing into turns
- metric scoring via Groq
- weighted overall score
- summary/strengths/improvements output

There’s no logic that classifies conversation segments into software-dev phases (like planning, implementation, debugging, testing, etc.).

You can see current scope in:

```213:228:c:\Users\HRISHIKESH\Desktop\Web development\workflow_eval\analyzer.py
def analyze_transcript(
    transcript: str,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    ...
    turns = parse_transcript(transcript)
    return evaluate_transcript_with_groq(
        turns=turns, model=model, api_key=api_key, weights=weights
    )
```

If you want, I can outline a clean phase-detection schema next (e.g., `phases_detected`, `phase_distribution`, `phase_timeline`) so you can add it when you switch back to Agent mode.

---

**User**

implement it

---

**Cursor**

I’ll implement phase detection in `analyzer.py` by adding a second Groq pass that classifies phases (planning, implementation, debugging, testing, etc.) and returns them in structured fields alongside your existing metrics. Then I’ll wire it into `analyze_transcript()`.

I’m adding phase detection directly into the analyzer output (with a defined phase taxonomy and normalized fields), while keeping your existing metric JSON unchanged so the app won’t break.

Implemented — `analyzer.py` now includes **phase detection**.

### What was added

- New phase taxonomy constant:
  - `problem_framing`, `planning`, `implementation`, `debugging`, `testing`, `refinement`
- Groq prompt now requests:
  - `phases_detected` (list)
  - `phase_distribution` (per-phase 0-1 values)
- Output normalization now:
  - filters unknown phases
  - deduplicates phase list
  - clamps distribution values to `[0,1]`
  - renormalizes distribution to sum to ~1
  - provides safe defaults when model output is incomplete

### Result format now includes phase fields

Alongside your existing metrics JSON, each result now also has:

- `phases_detected: List[str]`
- `phase_distribution: Dict[str, float]`

So yes — phase detection is now implemented in the analyzer layer.  
If you want, next I can update `app.py` to visualize `phase_distribution` as a bar chart per transcript.

---

**User**

yes do it

---

**Cursor**

I’ll update `app.py` to show detected phases and render `phase_distribution` as a bar chart for each transcript result.

Added phase visualization to `app.py` for each transcript result.

### New UI sections per transcript
- **Detected Phases**: shows `phases_detected` as a comma-separated list
- **Phase Distribution**: renders a bar chart from `phase_distribution`

This is now displayed inside each transcript’s result panel, along with your existing metrics/summary/strengths/improvements.

If the chart doesn’t appear in your installed Streamlit version, I can switch it to a guaranteed-compatible table + progress bars fallback.

---

**User**

okay we are almost close, now implement a summary table at top  when multiple files are uploaded showing all transcripts' scores side by side. This is explicitly mentioned as a bonus and is easy to add in app.py

---

**Cursor**

I’ll add a top-level summary table in `app.py` that appears when multiple files are analyzed, with one row per transcript and all key scores side by side.

Implemented in `app.py`.

### Added bonus summary table
When **more than one transcript** is uploaded/analyzed, the app now shows a top section:

- **Score Summary (All Transcripts)**

with rows per file and columns:

- `transcript`
- `prompt_clarity`
- `iteration_quality`
- `debugging_approach`
- `ai_utilization`
- `overall_score`

This appears above the per-transcript detailed expanders, so you can compare all files side by side quickly.

---

**User**

i think there isn't a metric bar chart per Transcript showing  the 4 metric scores visually

---

**Cursor**

You’re right — currently there is **no dedicated 4-metric bar chart per transcript**.

Right now per transcript you have:

- numeric metric cards (`st.metric`) for the 4 metrics + overall
- phase distribution bar chart
- text sections + raw JSON

So the missing piece is a separate chart for:
- `prompt_clarity`
- `iteration_quality`
- `debugging_approach`
- `ai_utilization`

If you switch to Agent mode, I can add this in `app.py` right under the metric cards using a small dataset like:

- x-axis: metric name
- y-axis: score (0–10)

and render with `st.bar_chart(...)` per transcript.

---

**User**

lets implement it

---

**Cursor**

I’ll add a per-transcript 4-metric bar chart right below the metric cards in `app.py`, then run a quick lint check.

Implemented. Each transcript now has a **4-metric bar chart** in its section.

### Added in `app.py`
Under the metric cards, I inserted a new block:

- **Metric Distribution**
- Bar chart for:
  - `prompt_clarity`
  - `iteration_quality`
  - `debugging_approach`
  - `ai_utilization`

So now every transcript has both:
- quick numeric cards
- visual metric comparison chart

The remaining warnings are still just unresolved dependency imports in the current lint environment.

---

**User**

we don't have confidence score right?

---

**Cursor**

Right — you currently **don’t have a confidence score** in the output schema.

Current analyzer result includes:

- `prompt_clarity`
- `iteration_quality`
- `debugging_approach`
- `ai_utilization`
- `overall_score`
- `phases_detected`
- `phase_distribution`
- `summary`
- `strengths`
- `improvements`
- optional `error`

No `confidence_score` (or similar) is being requested in the prompt or returned from `evaluate_transcript_with_groq()`.

If you want to add it later, common options are:

- **Model self-reported confidence** (ask Groq for `confidence_score: 0-1`)
- **Heuristic confidence** (based on transcript length, number of parsed turns, and parse quality)
- **Hybrid** (model confidence adjusted by heuristic penalties)

---

**User**

which one would be the best option for this app

---

**Cursor**

### Short answer

For this app, **a hybrid confidence score** is the best option:

- **Primary source**: have Groq output a `model_confidence` between 0–1 (or 0–100) for its own evaluation.
- **Heuristic adjustment**: down-weight that when your transcript signal is weak (e.g. very short, almost no user turns, or parse issues).

### Why hybrid is best here

- **Pure model self-report**  
  - **Pros**: simple, directly aligned with the model’s internal uncertainty.  
  - **Cons**: models tend to be overconfident; ignores obvious quality issues like “only 1 turn” or “no debugging content”.

- **Pure heuristic** (length, turn count, etc.)  
  - **Pros**: transparent, deterministic.  
  - **Cons**: doesn’t know anything about *semantic* quality (e.g., a long but nonsensical conversation might still get a high heuristic score).

- **Hybrid (recommended)**  
  - Use something like:
    \[
    \text{confidence} = \text{model_confidence} \times \text{signal\_quality\_factor}
    \]
  - `signal_quality_factor` can depend on:
    - number of total turns
    - balance of user vs AI turns
    - presence of multiple phases (if only one phase, maybe lower confidence)
  - This matches your app’s goal: **“How effectively is this engineer using AI?”** and acknowledges both:
    - how sure the model feels about its judgment
    - whether there was enough behavior to judge in the first place

If you’d like, I can sketch the exact JSON field(s) and a concrete formula for `signal_quality_factor` that you can drop into the analyzer.

---

**User**

implement it

---

**Cursor**

I’ll implement the hybrid confidence score in `analyzer.py` (model confidence + transcript signal quality adjustment) and surface it in `app.py` per transcript and in the summary table.

I’ve added hybrid confidence computation in the analyzer; next I’m wiring `confidence_score` into the app’s summary table and per-transcript metrics so it’s visible in UI.

Implemented hybrid confidence scoring end-to-end.

### What’s now in `analyzer.py`

- Added `model_confidence` request in the Groq prompt (`0..1`).
- Added heuristic `signal_quality_factor` (`0..1`) computed from transcript evidence:
  - number of turns
  - total content length
  - user presence
  - user/assistant balance
- Final confidence is computed as:

`confidence_score = model_confidence * signal_quality_factor`

- Added fields to returned JSON:
  - `confidence_score`
  - `model_confidence`
  - `signal_quality_factor`

Fallback/error outputs now also include these confidence fields (set to `0` where appropriate).

### What’s now in `app.py`

- In multi-file summary table, added:
  - `confidence_score`
- In each transcript panel, added a metric card:
  - **Confidence**

So confidence is now visible both in side-by-side comparison and per-transcript details.

Only remaining warnings are the same dependency-resolution warnings from your active lint environment (not logic errors).

---

**User**

confidence score is currently in range of 0-1, make in %

---

**Cursor**

I’ll update `analyzer.py` so `confidence_score` is returned as a **percentage (0–100)** instead of 0–1, and then adjust `app.py` to display it cleanly (including in the summary table).

Done.

### Changes made

- **`analyzer.py`**
  - `confidence_score` is now returned as a **percentage (0–100)**, rounded to 2 decimals:
    - previously: `0.0–1.0`
    - now: `0.0–100.0`

- **`app.py`**
  - Updated the metric label to **`Confidence (%)`** (value comes directly from `confidence_score`).

`model_confidence` and `signal_quality_factor` are still kept internally in `0–1` form (useful for debugging/inspection in the raw JSON), while the user-facing `confidence_score` is now in percent.

---

**User**

write the gitignore for this project

---

**Cursor**

I’ll add a practical Python/Streamlit `.gitignore` covering env files, virtual envs, caches, and editor/system artifacts for this project.

Added a solid `.gitignore` for your Python + Streamlit project.

It now ignores:

- env files (`.env`, `.env.*`) while allowing `.env.example`
- Python cache/bytecode (`__pycache__`, `*.pyc`, etc.)
- build artifacts (`build`, `dist`, `*.egg-info`)
- virtual environments (`.venv`, `venv`, `env`)
- test/tool caches (`.pytest_cache`, `.mypy_cache`, `.coverage`, etc.)
- Streamlit secrets (`.streamlit/secrets.toml`)
- editor/system junk (`.vscode`, `.idea`, `.DS_Store`, `Thumbs.db`)

If you want, I can also add ignores for uploaded transcript samples/output exports (if you plan to store them locally).

---

**User**

analyze all the files in directory & add only those in gitignore that is necessary

---

**Cursor**

I’ll scan the project directory contents and trim `.gitignore` so it only includes entries that are necessary for this repo’s current stack/files.

I checked the directory and it’s a very small app (`app.py`, `analyzer.py`, `requirements.txt`, `.env`, `.gitignore`), so I’ll slim `.gitignore` to a minimal set that’s actually necessary for this project type.

Done — I analyzed the current directory and reduced `.gitignore` to only the essentials for this project.

### Kept (necessary)
- `.env`
- `__pycache__/`, `*.py[cod]`
- virtual env folders: `.venv/`, `venv/`, `env/`
- `.streamlit/secrets.toml`
- OS junk: `.DS_Store`, `Thumbs.db`

### Removed (not necessary right now)
- packaging/build artifacts (`build/`, `dist/`, `*.egg-info/`, etc.)
- test/type/lint caches (`.pytest_cache/`, `.mypy_cache/`, etc.)
- editor-specific folders (`.idea/`, `.vscode/`, swap files)
- broad env pattern (`.env.*`) and `.env.example` exception

If you want, I can add back only one optional line: `.env.*` (useful if you’ll have `.env.local` or `.env.dev`).

---

**User**

inside the @README.md write short description of the project, setup instructions,etc

---

**Cursor**

I’ll add a concise `README.md` covering what the app does, setup steps, how to run it, and expected transcript format.

Added a concise `README.md` with:

- project purpose
- key features/metrics
- file structure
- setup instructions
- `.env` config (`GROQ_API_KEY`)
- run command (`streamlit run app.py`)
- usage steps
- transcript formatting tips for better parsing

If you want, I can also add a short “Known limitations” section (e.g., `.doc` may require extra system deps for `textract`).

---

**User**

refigure the project Structure in readme file coz in github repo its getting cluttered

---

**Cursor**


Checking the README's project structure section to simplify it for GitHub.




Replacing the wide ASCII tree and long inline comments with a compact layout that renders cleanly on GitHub.




Here’s what changed:

### Project structure (README)
- Replaced the long ASCII tree + inline comments with a **small table**: file, one-line purpose, and **clickable links** to `app.py`, `analyzer.py`, etc. so GitHub stays readable on narrow layouts.
- Clarified **local-only** `.env` in prose instead of stuffing it into the tree.
- Marked **`transcripts/`** as **optional** so the layout matches a minimal repo and doesn’t imply a folder you might not commit.

### Sample transcripts
- Reworded so it doesn’t claim a committed `transcripts/` bundle; it’s described as an optional local folder for testing.

If you later add a real `transcripts/` directory to the repo, you can add one row to the table (e.g. “sample inputs”).

