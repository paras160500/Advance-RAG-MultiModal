# ------------------------------------------------------------------------------
#


import time

import gradio as gr

from generation import generate_rag_response


def process_query_stream(query, search_type, model_type):
    """Process the query and stream the response more efficiently"""
    full_response = ""
    for chunk in generate_rag_response(query, search_type, 5, model_type, stream=True):
        full_response += chunk

        # Only yield every few characters to reduce UI updates
        if len(chunk) > 10 or chunk.endswith((".", "!", "?", "\n")):
            time.sleep(0.01)  # Small delay for smoother updates
            yield full_response

    # Ensure final text is always yielded
    yield full_response


def process_query_normal(query, search_type, model_type):
    """Process the query and return the complete response"""
    return generate_rag_response(query, search_type, 5, model_type, stream=False)


custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
    --ink: #1B2430;
    --ink-muted: #5B6472;
    --paper: #F7F6F2;
    --surface: #FFFFFF;
    --border: #E2DFD6;
    --accent: #2C5F6F;
    --accent-soft: #E7EFEF;
    --accent-2: #C9762B;
}

.gradio-container {
    background: var(--paper) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--ink) !important;
    max-width: 1600px !important;
    width: 96% !important;
    margin: 0 auto !important;
    padding-top: 28px !important;
}

/* ---------- Header ---------- */
#app-header { margin-bottom: 0 !important; padding-bottom: 4px; }
#app-header .eyebrow {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 999px;
    padding: 3px 12px;
    margin-bottom: 14px;
}
#app-header h1 {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    font-size: 2.4rem !important;
    letter-spacing: -0.01em;
    color: var(--ink) !important;
    margin: 0 0 6px 0 !important;
}
#app-subtitle { margin-top: 0 !important; }
#app-subtitle p {
    font-size: 1.02rem !important;
    color: var(--ink-muted) !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 22px;
}

/* ---------- Panels ---------- */
#control-panel, #answer-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 24px;
    box-shadow: 0 1px 2px rgba(27, 36, 48, 0.04);
}
#control-panel { border-top: 3px solid var(--accent); }
#answer-panel { border-top: 3px solid var(--accent-2); padding-top: 18px; }

.panel-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin-bottom: 14px !important;
}
.panel-label p { margin: 0 !important; color: var(--ink-muted) !important; }

/* ---------- Inputs ---------- */
#control-panel label span {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    color: var(--ink) !important;
}
#control-panel textarea, #control-panel input[type="text"] {
    background: var(--paper) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--ink) !important;
}
#control-panel textarea:focus, #control-panel input[type="text"]:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
#control-panel .info, #control-panel span[data-testid="block-info"] {
    color: var(--ink-muted) !important;
    font-size: 12px !important;
}

/* Radio pills */
#control-panel .wrap[role="radiogroup"] {
    gap: 8px !important;
}
#control-panel label.selected {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
#control-panel label.selected span {
    color: #FFFFFF !important;
}
#control-panel .wrap[role="radiogroup"] > label {
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    background: var(--paper) !important;
    padding: 6px 14px !important;
    transition: all 0.15s ease;
}

/* Checkbox */
#control-panel input[type="checkbox"] {
    accent-color: var(--accent) !important;
}

/* Submit button */
#submit-btn {
    background: var(--ink) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-size: 12.5px !important;
    padding: 12px 20px !important;
    box-shadow: 0 1px 2px rgba(27, 36, 48, 0.15);
    transition: transform 0.12s ease, box-shadow 0.12s ease;
}
#submit-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(27, 36, 48, 0.18);
    background: var(--accent) !important;
}

/* ---------- Answer box ---------- */
#answer-box {
    max-height: 560px;
    overflow-y: auto;
    padding: 4px 4px 4px 16px;
    border-left: 2px solid var(--accent-soft);
}
#answer-box h1, #answer-box h2, #answer-box h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
}
#answer-box p, #answer-box li { color: var(--ink); line-height: 1.65; }
#answer-box code {
    font-family: 'IBM Plex Mono', monospace !important;
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    border-radius: 4px;
    padding: 1px 5px;
}
#answer-box pre {
    background: var(--ink) !important;
    border-radius: 10px !important;
}
#answer-box pre code { background: transparent !important; color: #F7F6F2 !important; }
#answer-box blockquote {
    border-left: 3px solid var(--accent-2) !important;
    color: var(--ink-muted) !important;
    padding-left: 14px !important;
}
#answer-box a { color: var(--accent) !important; }

/* ---------- Examples ---------- */
#examples-section { margin-top: 8px; }
#examples-section table {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
#examples-section thead {
    background: var(--accent-soft) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase;
    font-size: 11px !important;
    letter-spacing: 0.06em;
}
#examples-section tbody tr:hover {
    background: var(--accent-soft) !important;
    cursor: pointer;
}

/* ---------- How-to ---------- */
#howto-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px 28px;
    margin-top: 18px;
}
#howto-card h3 {
    font-family: 'Fraunces', serif !important;
    font-size: 1.3rem !important;
    color: var(--ink) !important;
    margin-top: 0 !important;
}
#howto-card strong { color: var(--accent); }
#howto-card li { margin-bottom: 4px; color: var(--ink-muted); }
"""

# Create Gradio interface
with gr.Blocks(title="LocalRAG Q&A System", theme="soft", css=custom_css) as demo:
    with gr.Column(elem_id="app-header"):
        gr.Markdown(
            '<span class="eyebrow">Retrieval-Augmented Q&amp;A</span>\n\n# LocalRAG Q&A System'
        )
    gr.Markdown(
        "Ask questions about the RAG paper and get grounded, source-backed answers.",
        elem_id="app-subtitle",
    )

    with gr.Row():
        with gr.Column(scale=1, elem_id="control-panel"):
            gr.Markdown("Ask a question", elem_classes="panel-label")
            query_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask a question about Retrieval-Augmented Generation...",
                lines=4,
            )

            with gr.Row():
                search_type = gr.Radio(
                    ["keyword", "semantic", "hybrid"],
                    label="Search Method",
                    value="hybrid",
                    info="Choose how to retrieve relevant information",
                )

                model_type = gr.Radio(
                    ["gemini", "ollama"],
                    label="AI Model",
                    value="gemini",
                    info="Select which model generates your answer",
                )

            stream_checkbox = gr.Checkbox(
                label="Stream Response",
                value=True,
                info="See the answer as it's being generated",
            )

            submit_btn = gr.Button("Generate Answer", variant="primary", elem_id="submit-btn")

        with gr.Column(scale=2, elem_id="answer-panel"):
            gr.Markdown("Answer", elem_classes="panel-label")
            output = gr.Markdown(
                label="Answer",
                value="Your answer will appear here...",
                container=True,
                elem_id="answer-box",
            )

    # Handle form submission based on streaming preference
    def on_submit(query, search_type, model_type, stream):
        if not query.strip():
            yield "Please enter a question."
            return

        # Initial feedback to user
        yield "Retrieving relevant information..."

        if stream:
            yield from process_query_stream(query, search_type, model_type)
        else:
            yield process_query_normal(query, search_type, model_type)

    submit_btn.click(
        on_submit,
        inputs=[query_input, search_type, model_type, stream_checkbox],
        outputs=output,
        show_progress="minimal",  # Add this for visual feedback
    )

    # Add example questions
    with gr.Column(elem_id="examples-section"):
        gr.Markdown("Try an example", elem_classes="panel-label")
        gr.Examples(
            examples=[
                ["How does RAG work?", "hybrid", "gemini", True],
                [
                    "What are the benefits of RAG compared to fine-tuning?",
                    "semantic",
                    "gemini",
                    True,
                ],
                ["Explain RAG architecture with diagrams", "hybrid", "ollama", True],
                [
                    "What are common challenges in RAG implementations?",
                    "keyword",
                    "gemini",
                    False,
                ],
            ],
            inputs=[query_input, search_type, model_type, stream_checkbox],
        )

    with gr.Column(elem_id="howto-card"):
        gr.Markdown(
            """
        ### How to use this system

        1. **Enter your question** about Retrieval-Augmented Generation (RAG)
        2. Choose a **search method**:
           - **Keyword** — traditional text search
           - **Semantic** — meaning-based search using embeddings
           - **Hybrid** — combines keyword and semantic search
        3. Select an **AI model**:
           - **Gemini** — Google's Gemini 1.5 Flash model (requires API key)
           - **Ollama** — local Deepseek model running via Ollama
        4. Toggle **streaming** to see the response generated in real time

        The system retrieves relevant information from the indexed RAG paper and generates a comprehensive answer based on that information.
        """
        )

# Launch the app
if __name__ == "__main__":
    demo.queue().launch()