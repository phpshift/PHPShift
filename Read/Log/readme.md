**Name**
Read.Log

**Goal**
To provide an AI-powered analysis and summary of specified log files within a project's system folder.

**Functionality**
This skill scans the `{project}/.system/` directory for log files (e.g., `api.log`). It then presents a selection of these logs to the user, allowing them to choose one for analysis. Upon selection, the skill uses AI to analyze the chosen log file's content, combined with the user's request, to generate a markdown-formatted summary of key issues, errors, or anomalies. This summary is saved as `summary.md` in the project's root directory.

**Returns**
The markdown content of the generated `summary.md` file, or `False` if no log files are found or the user cancels the operation.