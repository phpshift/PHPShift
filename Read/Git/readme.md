**Name**
Read.Git

**Goal**
To allow users to interact with Git repositories by converting natural language requests into Git commands, executing them and summarizing the output.

**Functionality**
This skill translates a user's natural language request into an executable Git CLI command. It then executes this command within the project's Git repository and generates a concise Markdown summary of the command's output. The summary is saved as `summary.md` in the project root and is automatically opened in the code editor for immediate review.

**Returns**
The text content of the generated `summary.md` file.