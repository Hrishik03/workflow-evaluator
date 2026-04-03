import streamlit as st
from analyzer import analyze_transcript
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text_from_file(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if suffix in {".txt", ".md"}:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    if suffix == ".docx":
        doc = Document(BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()

    if suffix == ".doc":
        # Legacy .doc support uses optional textract if available.
        try:
            import tempfile
            import textract

            with tempfile.NamedTemporaryFile(delete=False, suffix=".doc") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            text = textract.process(tmp_path).decode("utf-8", errors="ignore")
            return text.strip()
        except Exception as exc:
            raise RuntimeError(
                "Legacy .doc parsing requires textract and system dependencies. "
                "Convert to .docx/.txt or install textract dependencies."
            ) from exc

    raise ValueError("Unsupported file format. Please upload pdf, txt, md, doc, or docx.")


def main() -> None:
    st.set_page_config(page_title="AI Workflow Evaluator", page_icon=":mag:")
    st.title("AI Workflow Evaluator")
    st.write("Upload one or more transcript files to evaluate AI usage during software development.")

    uploaded_files = st.file_uploader(
        "Upload transcript(s)",
        type=["pdf", "txt", "md", "doc", "docx"],
        accept_multiple_files=True,
        help="Supported formats: PDF, TXT, MD, DOC, DOCX",
    )

    if not uploaded_files:
        return

    st.write(f"Uploaded {len(uploaded_files)} file(s).")

    # Extract text, but DO NOT start analysis until user clicks the button.
    extracted_transcripts = []
    for f in uploaded_files:
        try:
            extracted = extract_text_from_file(f)
            if extracted.strip():
                extracted_transcripts.append({"file_name": f.name, "transcript": extracted})
            else:
                st.warning(f"No readable text found in `{f.name}`.")
        except Exception as exc:
            st.error(f"Could not parse `{f.name}`: {exc}")

    if not extracted_transcripts:
        st.warning("No readable transcript content found in the uploaded files.")
        return

    analyze_clicked = st.button("Analyze all uploaded transcripts")
    if not analyze_clicked:
        return

    with st.spinner("Analyzing transcripts..."):
        results = []
        for item in extracted_transcripts:
            file_result = analyze_transcript(item["transcript"])
            results.append({"file_name": item["file_name"], "result": file_result})

    if len(results) > 1:
        st.subheader("Score Summary (All Transcripts)")
        summary_rows = []
        for entry in results:
            result = entry["result"]
            summary_rows.append(
                {
                    "transcript": entry["file_name"],
                    "prompt_clarity": result.get("prompt_clarity", 0),
                    "iteration_quality": result.get("iteration_quality", 0),
                    "debugging_approach": result.get("debugging_approach", 0),
                    "ai_utilization": result.get("ai_utilization", 0),
                    "overall_score": result.get("overall_score", 0.0),
                    "confidence_score": result.get("confidence_score", 0.0),
                }
            )
        st.dataframe(summary_rows, use_container_width=True)

    st.subheader("Transcript Evaluations")
    for i, entry in enumerate(results, start=1):
        file_name = entry["file_name"]
        result = entry["result"]

        with st.expander(f"{i}. {file_name}", expanded=(i == 1)):
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Prompt Clarity", result.get("prompt_clarity", 0))
            c2.metric("Iteration Quality", result.get("iteration_quality", 0))
            c3.metric("Debugging Approach", result.get("debugging_approach", 0))
            c4.metric("AI Utilization", result.get("ai_utilization", 0))
            c5.metric("Overall Score", result.get("overall_score", 0.0))
            c6.metric("Confidence (%)", result.get("confidence_score", 0.0))

            st.markdown("**Metric Distribution**")
            metric_chart_data = [
                {"metric": "prompt_clarity", "score": result.get("prompt_clarity", 0)},
                {"metric": "iteration_quality", "score": result.get("iteration_quality", 0)},
                {"metric": "debugging_approach", "score": result.get("debugging_approach", 0)},
                {"metric": "ai_utilization", "score": result.get("ai_utilization", 0)},
            ]
            st.bar_chart(metric_chart_data, x="metric", y="score")

            st.markdown("**Detected Phases**")
            phases_detected = result.get("phases_detected", [])
            if phases_detected:
                st.write(", ".join(phases_detected))
            else:
                st.write("No phases detected.")

            st.markdown("**Phase Distribution**")
            phase_distribution = result.get("phase_distribution", {})
            if phase_distribution:
                phase_chart_data = [
                    {"phase": phase, "share": share}
                    for phase, share in phase_distribution.items()
                ]
                st.bar_chart(phase_chart_data, x="phase", y="share")
            else:
                st.write("No phase distribution returned.")

            st.markdown("**Summary**")
            st.write(result.get("summary", ""))

            st.markdown("**Strengths**")
            strengths = result.get("strengths", [])
            if strengths:
                for item in strengths:
                    st.write(f"- {item}")
            else:
                st.write("No strengths returned.")

            st.markdown("**Improvements**")
            improvements = result.get("improvements", [])
            if improvements:
                for item in improvements:
                    st.write(f"- {item}")
            else:
                st.write("No improvements returned.")

            if result.get("error"):
                st.warning(f"Analyzer note: {result['error']}")

            # st.markdown("**Raw JSON result**")
            # st.json(result)


if __name__ == "__main__":
    main()