**Name**
Read.Database

**Goal**
To allow users to query the database using natural language, execute the query, and provide a summarized response.

**Functionality**
This skill takes a user's natural language request, converts it into a MySQL query statement and parameters using AI, executes the query against the database, and then uses a second AI to summarize the database's response. The summary is saved to a Markdown file in the project folder and displayed to the user.

**Returns**
The content of the generated `summary.md` file, which summarizes the database query results.