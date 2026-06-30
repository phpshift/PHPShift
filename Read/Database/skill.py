from imports import *


class ReadDatabase:
    def run(self, message="", project="", skill=""):
        cli.setLoading("Reading database")

        prompt_sql_generation = AISI.prompt(message, skill)
        generated_files = AISI.FILES(prompt_sql_generation)

        statement = generated_files.get("statement.sql", "").strip()
        params_json = generated_files.get("params.json", "{}").strip()

        if not statement:
            return cli.error("AI failed to generate a SQL statement. Please refine your request.")

        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            return cli.error("AI generated invalid JSON for parameters. Please check the prompt rules.")

        cli.trace(f"Executing SQL statement: {statement}")
        cli.trace(f"With parameters: {params}")

        db_response = DB.query(statement, params=params if params else None)
        summary_prompt_content = f"""
**Definition**

You are an AI assistant specialized in summarizing database query results.
You have to analyze the provided database query response and generate a concise and informative summary in Markdown format.

**Consider**

This is the database query response in JSON format:
```json
{json.dumps(db_response, indent=2)}
```

**Required**

I need you to generate a `summary.md` file that explains the data in an easily understandable way. Highlight key findings or relevant information.

**Rules**

Follow these rules:

- The summary must be in Markdown format.
- The summary should be concise and focus on the most important aspects of the data.
- Do not include the raw JSON data in the summary.
- The output should only be the content for `summary.md`.

**Request**
{message}

Generate a summary for the above database response.
"""
        summary_files = AISI.FILES(summary_prompt_content)
        summary_content = summary_files.get("summary.md", "").strip()

        if not summary_content:
            return cli.error("AI failed to generate a summary for the database response.")

        summary_path = f"{project}/summary.md"
        Patch.add(path=summary_path)
        cli.write(file=summary_path, content=summary_content)

        cli.command(f"code {summary_path}", False, True)

        return summary_content