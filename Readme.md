# Lesson 13 practical application: File Insight Assistant

Build a small command-line assistant that reads a local file with the Claude Agent SDK and produces a report with findings, evidence, and limits. The example follows the lesson's workflow: **scope → read → analyze → report**.

Imagine joining a project with release notes, an unfamiliar Python script, sales data, and a support policy. This assistant helps you understand each source without asking it to edit files or execute the source code.

## What you will learn

| Lesson concept | What the application demonstrates |
| --- | --- |
| Separate reading from analysis | `Read` retrieves text; Claude reasons about the retrieved content. |
| Summarize faithfully | Preserve conditional approvals, owners, deadlines, and unfinished work. |
| Explain Python using evidence | Identify functions and calls; distinguish definitions from invocation. |
| Analyze CSV and JSON | Inspect structure, show supported totals, and keep null distinct from zero. |
| Answer file-based questions | Cite sections and acknowledge when a file does not contain the answer. |
| Observe the agent loop | Follow readable Scope, Read, Analyze, and Report messages; use `--verbose` for raw SDK details. |
| Verify the outcome | Reject failed/incomplete runs and answers without an observed successful target-file read. |

The assistant asks for citations and coverage information. Those instructions guide the model; they do not automatically validate every claim. You still compare the report with its source.

## Project files

```text
practical_application/
├── app.py                   # Command-line interface and agent loop
├── verify_data.py           # Independent CSV/JSON checks; no API required
├── requirements.txt        # SDK version used for this example
├── Readme.md
├── tests/
│   └── test_application.py  # Offline checks with simulated SDK messages
└── sample_project/
    ├── release_notes.txt
    ├── policy.txt
    ├── app.py              # Example source to analyze, not the assistant
    ├── input.txt
    ├── sales.csv
    └── order.json
```

## Configure the application

Use Python 3.10 or later. The example was checked locally with Python 3.14 and `claude-agent-sdk==0.2.175`. Live analysis requires network access and configured Anthropic authentication. API calls use your account's available credits and billing.

### Windows PowerShell

Open a terminal in this `practical_application` folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "your-anthropic-api-key"
```

The commands below use the virtual environment's Python directly, so activating the environment is optional. The environment variable above applies to the current terminal. Use your own key locally; no credentials are included in the application.

### macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

For the run commands below, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` on macOS/Linux.

The SDK uses a bundled Claude Code binary on supported wheel installations. If your installation lacks it, install Claude Code separately and make it available on `PATH`. A separate Node.js installation is not needed for the bundled Python SDK binary. See the [official setup instructions](https://code.claude.com/docs/en/agent-sdk/quickstart).

The application does not load `.env` files. Set the variable in the terminal that launches it. No model is hard-coded: the SDK chooses its default unless you pass `--model` or set `CLAUDE_MODEL`.

```powershell
$env:CLAUDE_MODEL = "your-supported-model-id"
```

## Run the application

Run these commands from this folder. Source paths are resolved relative to `sample_project`, regardless of the terminal's working directory.

### Output designed for teaching

Each run starts with a lesson topic, source file, learning goal, and key concept.
The terminal then explains the workflow as the agent runs:

```text
[1/4 SCOPE] Source and task validated. Starting the agent...
[2/4 READ] Agent requested policy.txt through the Read tool.
[2/4 READ] Tool returned source text to the agent.
[3/4 ANALYZE] Waiting for Claude's analysis of the retrieved text...
[4/4 REPORT] Run completed in 2 agent turns.
```

This is an illustrative trace, not a live transcript. Read messages may repeat
when the agent retrieves more text. The Analyze message indicates that the host
is waiting for an answer after retrieval; it does not expose the model's internal
reasoning. The completion message appears only after the host's run checks pass.

The requested Markdown report has four sections:

1. **Findings — What did we learn?** A direct answer, with a function table and
   call flow for code, or fields and supported calculations for data.
2. **Concept explained — Why does it matter?** A short beginner explanation with
   a cited example from the source.
3. **Evidence — Where can we check?** Source references for the main claims.
4. **Limits — What do we still not know?** Coverage, inferences, and missing facts.

These sections are model instructions, not a strict output-schema guarantee.
After the report, a discussion question helps students check their understanding.
The lesson guide and progress messages go to stderr; stdout and saved Markdown
contain only the model's report. No additional formatting dependencies are needed.

For a lesson about the SDK itself, include the raw tool calls, matching tool
result IDs, and completion metadata:

```powershell
.\.venv\Scripts\python.exe app.py ask --question "Who owns escalations?" --verbose
```

### 1. Preview a prompt without an API call

```powershell
.\.venv\Scripts\python.exe app.py summarize --dry-run
```

This prints the working directory, selected tool, turn limit, system instructions, and task prompt. It does not read source contents into the prompt or generate an analysis. You can also run `python app.py summarize --dry-run` before installing the SDK.

### 2. Summarize release notes

```powershell
.\.venv\Scripts\python.exe app.py summarize
.\.venv\Scripts\python.exe app.py summarize --audience "a software developer"
```

The default source is `release_notes.txt`. Check that the report preserves the billing-check condition on Friday's launch, Ravi's ownership, and the pending rollback plan.

### 3. Explain the Python example

```powershell
.\.venv\Scripts\python.exe app.py explain
```

The source is `sample_project/app.py`. It defines `read_file`, `process_text`, and `main`. The report should explain what would happen **if `main()` were called**, and note that the file contains no such call. This assistant inspects the code; it does not run it.

### 4. Analyze CSV and JSON

```powershell
.\.venv\Scripts\python.exe app.py data
.\.venv\Scripts\python.exe app.py data --file order.json
```

The CSV has three data rows. Notebook totals 3 units and Pen totals 3 units. Revenue is unavailable because the file has no prices. The JSON describes order 42 as pending with `total: null`; null is not zero.

Recheck those observations using ordinary Python:

```powershell
.\.venv\Scripts\python.exe verify_data.py
```

This script computes results from the actual sample files. It does not call Claude and does not depend on its report.

### 5. Ask questions with evidence

```powershell
.\.venv\Scripts\python.exe app.py ask --question "Who owns escalations?"
.\.venv\Scripts\python.exe app.py ask --question "What is the weekend schedule?"
```

The default source is `policy.txt`. The first answer should cite Section 3: the operations team owns escalations. The weekend schedule is not specified. These are reference expectations for the supplied files, not a transcript of a live model run.

### 6. Save a successful report

```powershell
.\.venv\Scripts\python.exe app.py summarize --output reports/release-summary.md
```

The Python host saves the final text after checking completion and observed tool feedback. It creates the report directory as needed and refuses to overwrite an existing file. Reports must be outside `sample_project` to keep them separate from inputs.

### Use your own file

Copy a suitable text, Markdown, Python, CSV, or JSON file into `sample_project`, then select it:

```powershell
.\.venv\Scripts\python.exe app.py summarize --file my_notes.txt
.\.venv\Scripts\python.exe app.py ask --file my_notes.txt --question "Which decisions are still open?"
```

Each mode checks the input type. The CLI rejects missing files and paths outside `sample_project`, including resolved paths that escape through links. This validates the requested input; it is not an operating-system sandbox around the SDK's tools. `cwd` selects the working directory. Use the included non-sensitive samples for the exercise.

## How the application was built

### Step 1: Separate inputs from application code

```python
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR / "sample_project"
```

Anchoring paths to the script keeps behavior consistent when students launch the application from another folder. `resolve_target()` checks that the selected source exists, stays inside this directory, and has a suitable extension.

### Step 2: Turn the question into a task contract

`build_prompt()` combines the exact source path with a mode-specific task and a shared report format:

```python
prompt = build_prompt("ask", target, "Who owns escalations?", "a project manager")
```

The generated prompt asks for `Findings`, `Concept explained`, `Evidence`, and `Limits` in beginner-friendly language. For summaries, it requests conditions and unfinished work. For code, it requests a function table and numbered call flow. For data, it requests fields and supported calculations. The concept explanation uses a cited example from the source. This gives the model a concrete objective before it reads anything.

The application does not paste the source into the prompt: the agent must request the file through `Read`. `SYSTEM_PROMPT` also tells it to treat file text as source material rather than task instructions.

### Step 3: Configure a focused tool surface

This excerpt from `make_options()` shows the core configuration:

```python
options = ClaudeAgentOptions(
    cwd=str(PROJECT_DIR.resolve()),
    tools=["Read"],
    allowed_tools=["Read"],
    max_turns=5,
    system_prompt=SYSTEM_PROMPT,
    setting_sources=[],
    mcp_servers={},
    strict_mcp_config=True,
)
```

`tools` selects built-in tools; `allowed_tools` preapproves their use. The settings and MCP options keep this example independent of external tool configuration. `max_turns` limits agent turns, not file count. The full function also forwards an optional model selection. See the [Python options reference](https://code.claude.com/docs/en/agent-sdk/python#claudeagentoptions) and [SDK type definitions](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py).

### Step 4: Observe the asynchronous agent loop

```python
options = make_options(max_turns, model)
return await collect_report(query(prompt=prompt, options=options), target)
```

`query()` yields messages as the agent progresses. Inside `collect_report()`, the application observes:

```python
if isinstance(message, AssistantMessage):
    for block in message.content:
        if isinstance(block, ToolUseBlock):
            # Record a Read request for the selected file and its block.id.
            ...
elif isinstance(message, UserMessage) and isinstance(message.content, list):
    for block in message.content:
        if isinstance(block, ToolResultBlock):
            # Match block.tool_use_id to the earlier request.
            ...
```

These comments and ellipses abbreviate the complete implementation in `app.py`. The application checks whether `UserMessage.content` is a list before iterating it. Matching IDs connect tool feedback to its request, and a failed read does not count as retrieved evidence. Printing a tool request observes it; the SDK executes the tool.

The terminal explains each workflow step on standard error. With `--verbose`, it also shows `[TOOL CALL]`, `[TOOL RESULT]`, and `[RUN]` messages. The final report goes to standard output.

### Step 5: Check completion before accepting the answer

```python
if final is None:
    raise RuntimeError("The stream ended without a ResultMessage. No report accepted.")
if final.is_error or final.subtype != "success":
    raise RuntimeError("Agent run did not complete successfully.")
if not final.result or not final.result.strip():
    raise RuntimeError("The run returned no final report.")
if not successful_reads:
    raise RuntimeError("No successful Read result for the requested file was observed.")
```

This shortened excerpt keeps the same acceptance checks as the implementation. A tool response alone is not completion, and plausible final text alone does not show that the source was retrieved. A successful Read still does not prove complete coverage or correct reasoning: check the citations and reported limits yourself.

SDK launch and transport exceptions produce a readable terminal error. An incomplete run exits with status 1; invalid command syntax uses status 2. A successful run uses status 0. Cancelling with Ctrl+C uses status 130.

### Step 6: Verify arithmetic independently

In `verify_data.py`, Python's standard CSV parser reads the sample rows and adds integer units by item:

```python
totals[row["item"]] += units
```

The JSON parser preserves a null total as Python `None`:

```python
"total_is_null": order["total"] is None
```

The checker expects the supplied CSV schema and reports invalid whole-number units. It also rejects a missing JSON `total` field instead of silently treating absence as explicit null. Its narrow scope makes it easy to compare these calculations with the agent's interpretation.

## Test the application without API calls

After installing the requirements, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use real SDK message classes and simulated asynchronous streams. They cover successful retrieval, failed reads, mismatched IDs, reads of another file, turn-limit errors, missing/empty final results, input validation, prompt previews, and independent data checks. They do not contact Anthropic or verify live model behavior.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| SDK is missing | Install `requirements.txt` with the same Python interpreter used to launch the app. |
| Authentication or account error | Set a valid `ANTHROPIC_API_KEY` in the current terminal and check account access/credits. |
| Claude Code binary is missing | Follow the official setup link above; ensure a supported bundled wheel or a native installation on `PATH`. |
| `error_max_turns` | Inspect tool feedback; retry with `--max-turns 8` if more turns are justified. |
| No successful Read observed | Review tool feedback and permissions. The app deliberately refuses to accept an ungrounded final report. |
| Existing output file | Choose another `--output` filename. |
| Partial file coverage | Narrow the question or request the missing portion; do not claim a complete review. |

## Exercises

1. Compare a manager summary with a developer summary. Which facts remain unchanged?
2. Add a named owner to the rollback issue and check that the report updates its evidence.
3. Add a call to `main()` in the sample Python file and compare the static explanation. Reading still does not prove successful execution.
4. Change the JSON total from `null` to `0`, then compare both the agent's report and `verify_data.py` output.
5. Add a weekend schedule section to the policy and ask the previously unanswered question again.
