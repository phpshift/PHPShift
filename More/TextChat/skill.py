from imports import *


class MoreTextChat:
    _history_initialized = False

    ####################################################################################// Main
    def run(self, message="", project="", skill=""):
        # Reset chat history on first execution of PHPShift startup
        if not MoreTextChat._history_initialized:
            self.__resetChatHistory(project)
            MoreTextChat._history_initialized = True

        if not message or not message.strip():
            cli.error("Message is required for Text Chat")
            return False

        # Load existing chat history
        history = self.__loadChatHistory(project)

        # Run AI thinker to determine category and execution plan
        decision = self.__think(message, history)
        category = decision.get("category", "General")

        cli.trace(f"Text Chat category: {category}")

        action_log = []

        # ── 1. General Mode ──────────────────────────────────────────────────
        if category == "General":
            reply = decision.get("reply", "").strip()
            if not reply:
                cli.setLoading("Generating reply")
                prompt = (
                    f"Conversation History:\n{self.__formatHistoryForPrompt(history)}\n\n"
                    f"User Message:\n{message}\n\n"
                    "Provide a helpful, friendly, and concise response to the user."
                )
                reply = AISI.REPLY(prompt).strip()

            if not reply:
                reply = "I understand your message. How else can I assist you with your PHPShift project?"

            print()
            cli.info("PHPShift: " + reply)
            self.__speakResponse(reply)
            print()

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": reply})
            self.__saveChatHistory(history, project)
            return True

        # ── 2. Building Mode ─────────────────────────────────────────────────
        elif category == "Building":
            skills_queue = decision.get("skills", [])
            if not skills_queue:
                available = AISI.list(skip=["More.TextChat", "Render"])
                skills_queue = [{"skill": s, "message": message} for s in available if s in message]

            if not skills_queue:
                cli.trace("No building skills identified; falling back to general reply")
                return self.__handleGeneralFallback(message, history, project)

            for step in skills_queue:
                chosen_skill = step.get("skill", "").strip()
                step_message = step.get("message", message).strip() or message

                cli.setLoading(f"Running: {chosen_skill}")
                cli.trace(f"Executing building skill: {chosen_skill} | message: {step_message}")

                try:
                    res = AISI.run(step_message, chosen_skill)
                    if res:
                        action_log.append(f"Ran '{chosen_skill}' with message \"{step_message}\" — completed successfully.")
                    else:
                        action_log.append(f"Ran '{chosen_skill}' with message \"{step_message}\" — finished.")
                except Exception as e:
                    action_log.append(f"Ran '{chosen_skill}' — error: {e}")
                    cli.error(f"Skill '{chosen_skill}' error: {e}")

            cli.setLoading("Composing reply")
            final_reply = self.__composeSummaryReply(message, history, action_log)

            print()
            cli.info("PHPShift: " + final_reply)
            self.__speakResponse(final_reply)
            print()

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": final_reply})
            self.__saveChatHistory(history, project)
            return True

        # ── 3. Fixing Mode (Mandatory More.FixProblem) ───────────────────────
        elif category == "Fixing":
            cli.setLoading("Collecting project info")
            file_tree, log_content = self.__collectProjectInfo(project)

            info_parts = [f"User reported problem:\n{message}"]
            if file_tree:
                info_parts.append(f"Project file tree:\n```yaml\n{file_tree}\n```")
            if log_content:
                info_parts.append(f"Application log files:\n```\n{log_content}\n```")
            else:
                info_parts.append("Note: Project logs were checked. No relevant error logs were found.")

            enriched_message = "\n\n".join(info_parts)

            cli.setLoading("Running: More.FixProblem")
            cli.trace(f"Invoking More.FixProblem with collected project info")

            try:
                res = AISI.run(enriched_message, "More.FixProblem")
                if res:
                    action_log.append("Ran 'More.FixProblem' with collected file tree and logs — fix applied.")
                else:
                    action_log.append("Ran 'More.FixProblem' with collected file tree and logs — process finished.")
            except Exception as e:
                action_log.append(f"Ran 'More.FixProblem' — error: {e}")
                cli.error(f"More.FixProblem error: {e}")

            cli.setLoading("Composing reply")
            final_reply = self.__composeSummaryReply(message, history, action_log)

            print()
            cli.info("PHPShift: " + final_reply)
            self.__speakResponse(final_reply)
            print()

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": final_reply})
            self.__saveChatHistory(history, project)
            return True

        return True

    ####################################################################################// Thinking & Flow
    def __think(self, message="", history=[]):
        """Single-pass chat thinker: categorise message into General, Building, or Fixing."""
        cli.setLoading("Thinking")

        history_formatted = self.__formatHistoryForPrompt(history)
        available_skills = AISI.list(skip=["More.TextChat", "Render"])
        skills_formatted = "\n".join(f"- {s}" for s in available_skills) if available_skills else "None"

        thinker_prompt = (
            "You are the intelligent central thinker for the PHPShift development CLI.\n"
            "Analyse the user's message, considering the chat history context and available skills.\n\n"
            f"Chat History:\n{history_formatted}\n\n"
            f"User Message:\n\"{message}\"\n\n"
            f"Available Skills:\n{skills_formatted}\n\n"
            "Categorise the user request into exactly ONE of the three categories:\n"
            "1. \"General\": The user is asking a general chat question, greeting, or seeking information/guidance that does not require building or fixing.\n"
            "2. \"Building\": The user is describing the implementation of a new solution, feature, page, API, cron job, or improvement.\n"
            "3. \"Fixing\": The user is describing a problem, bug, error, exception, or unexpected behavior in their application.\n\n"
            "Return ONLY a JSON object with this exact structure:\n"
            "{\n"
            '  "category": "General" | "Building" | "Fixing",\n'
            '  "reply": "Your complete helpful reply to the user if category is General, otherwise empty string",\n'
            '  "skills": [\n'
            '    {"skill": "Skill.Name", "message": "Specific instruction to pass to that skill"}\n'
            '  ]\n'
            "}\n\n"
            "Rules:\n"
            "- For \"General\": Set category to \"General\", provide the complete response in \"reply\", set \"skills\" to [].\n"
            "- For \"Building\": Set category to \"Building\", set \"reply\" to \"\", select relevant skill(s) from Available Skills in execution order with tailored instructions in \"skills\".\n"
            "- For \"Fixing\": Set category to \"Fixing\", set \"reply\" to \"\", set \"skills\" to [].\n"
            "- Return ONLY raw valid JSON. Do NOT include markdown code fences or extra commentary."
        )

        raw = AISI.REPLY(thinker_prompt)
        cli.trace(f"Thinker raw response: {raw}")

        return self.__parseThinkerResponse(raw)

    def __parseThinkerResponse(self, raw=""):
        if not raw:
            return {"category": "General", "reply": "", "skills": []}

        cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("`").strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                category = parsed.get("category", "General").strip().capitalize()
                if category not in ["General", "Building", "Fixing"]:
                    category = "General"

                reply = str(parsed.get("reply", "")).strip()

                skills = []
                raw_skills = parsed.get("skills", [])
                if isinstance(raw_skills, list):
                    for item in raw_skills:
                        if isinstance(item, dict):
                            s = str(item.get("skill", "")).strip()
                            m = str(item.get("message", "")).strip()
                            if s:
                                skills.append({"skill": s, "message": m})

                return {"category": category, "reply": reply, "skills": skills}
        except Exception as e:
            cli.trace(f"Could not parse thinker JSON response: {e}")

        raw_upper = raw.upper()
        if "FIXPROBLEM" in raw_upper or "FIXING" in raw_upper or "BUG" in raw_upper or "ERROR" in raw_upper:
            return {"category": "Fixing", "reply": "", "skills": []}

        return {"category": "General", "reply": raw, "skills": []}

    def __handleGeneralFallback(self, message="", history=[], project=""):
        cli.setLoading("Generating reply")
        prompt = (
            f"Conversation History:\n{self.__formatHistoryForPrompt(history)}\n\n"
            f"User Message:\n{message}\n\n"
            "Provide a clear, helpful response to the user."
        )
        reply = AISI.REPLY(prompt).strip() or "I understand your message. How else can I assist you with your PHPShift project?"

        print()
        cli.info("PHPShift: " + reply)
        self.__speakResponse(reply)
        print()

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        self.__saveChatHistory(history, project)
        return True

    def __speakResponse(self, text=""):
        if getattr(cli, "mode", "text") == "voice" and text and text.strip():
            try:
                cli.speak(text.strip())
            except Exception as e:
                cli.trace(f"Speech output error: {e}")

    def __composeSummaryReply(self, message="", history=[], action_log=[]):
        actions_summary = "\n".join(action_log) if action_log else "Executed requested task."
        history_formatted = self.__formatHistoryForPrompt(history)

        reply_prompt = (
            "You are a helpful AI assistant integrated into the PHPShift development tool.\n"
            "You have executed development skill(s) to fulfill the user's request.\n"
            "Summarise what was done and the outcome clearly and concisely for the user.\n\n"
            f"Chat History:\n{history_formatted}\n\n"
            f"User's Message:\n{message}\n\n"
            f"Actions Taken:\n{actions_summary}\n\n"
            "Rules:\n"
            "- Be friendly, clear, and direct.\n"
            "- Summarise the outcome in 2 to 5 sentences.\n"
            "- Explain next steps or what the user should check if relevant."
        )

        reply = AISI.REPLY(reply_prompt)
        return reply.strip() if reply and reply.strip() else "Task completed successfully."

    ####################################################################################// Project Context & Logs
    def __collectProjectInfo(self, project=""):
        """Collect file tree and log content to enrich FixProblem message."""
        file_tree = ""
        if project and os.path.exists(project):
            skip_dirs = {".git", ".system", "vendor", "node_modules"}
            lines = []
            for root, dirs, files in os.walk(project):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                rel_root = os.path.relpath(root, project).replace("\\", "/")
                prefix = "" if rel_root == "." else rel_root + "/"
                for filename in sorted(files):
                    if not filename.startswith("x.") and not filename.startswith("."):
                        lines.append(prefix + filename)
            file_tree = "\n".join(lines)

        log_content = ""
        space_dir = os.path.join(project, "Space") if project else ""
        if os.path.isdir(space_dir):
            log_parts = []
            for fname in sorted(os.listdir(space_dir)):
                if fname.endswith(".log"):
                    fpath = os.path.join(space_dir, fname)
                    content = cli.read(fpath) or ""
                    content = content.strip()
                    if content:
                        tail = "\n".join(content.splitlines()[-100:])
                        log_parts.append(f"--- {fname} ---\n{tail}")
            log_content = "\n\n".join(log_parts)

        return file_tree, log_content

    ####################################################################################// Chat History Persistence
    def __getChatFilePath(self, project=""):
        proj_dir = project if (project and os.path.exists(project)) else (Help.cwd if Help.cwd else os.getcwd())
        return os.path.join(proj_dir, ".system/chat.json").replace("\\", "/")

    def __resetChatHistory(self, project=""):
        file_path = self.__getChatFilePath(project)
        try:
            cli.write(file_path, json.dumps([], indent=2))
            cli.trace(f"Chat history reset: {file_path}")
        except Exception as e:
            cli.trace(f"Could not reset chat history: {e}")

    def __loadChatHistory(self, project=""):
        file_path = self.__getChatFilePath(project)
        if not os.path.exists(file_path):
            return []
        try:
            content = cli.read(file_path)
            if not content or not content.strip():
                return []
            history = json.loads(content)
            return history if isinstance(history, list) else []
        except Exception as e:
            cli.trace(f"Could not load chat history: {e}")
            return []

    def __saveChatHistory(self, history, project=""):
        file_path = self.__getChatFilePath(project)
        try:
            cli.write(file_path, json.dumps(history, indent=2, ensure_ascii=False))
            cli.trace(f"Saved chat history to {file_path}")
        except Exception as e:
            cli.trace(f"Could not save chat history: {e}")

    def __formatHistoryForPrompt(self, history):
        if not history:
            return "No previous conversation history."
        lines = []
        recent = history[-10:]
        for item in recent:
            role = "User" if item.get("role") == "user" else "Assistant"
            content = str(item.get("content", "")).strip()
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
