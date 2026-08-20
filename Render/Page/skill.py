from imports import *


class RenderPage:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Rendering the page")

        group = "public"
        page = "page"
        internal = False

        if isinstance(message, dict) and "description" in message:
            group = message["group"]
            page = message["page"]
            internal = message["internal"]
            message = message["description"]

        try:
            pages_dir = f"{project}/Pages"
            if os.path.exists(pages_dir):
                pages = [
                    p
                    for p in os.listdir(pages_dir)
                    if os.path.isdir(os.path.join(pages_dir, p))
                    and p not in ["public.phpshift", "x.placeholder"]
                    and not p.startswith("x.")
                ]

                if (
                    pages
                    and not getattr(VAR, "reference", None)
                    and not getattr(VAR, "styling", None)
                ):
                    cli.trace("Selecting reference page using AI")
                    page_list_str = ", ".join(pages)
                    select_prompt = (
                        f"User request for creating new page: '{message}'\n"
                        f"Available existing pages: {page_list_str}\n"
                        f"Select the single existing page name from the list above to use as a visual and structural reference for generating the new page.\n"
                        f"Respond with ONLY the exact page name from the list, or 'NONE' if no page is suitable."
                    )
                    reply = AISI.REPLY(select_prompt).strip()
                    selected_page = ""
                    for p in pages:
                        if p.lower() in reply.lower():
                            selected_page = p
                            break
                    if selected_page:
                        VAR.reference = selected_page
                        VAR.styling = selected_page

            prompt = AISI.prompt(message, skill)
            code = AISI.FILES(prompt)
            if not code:
                return False

            Help.codeEditor(group, page, code, internal)
            Help.updateSitemap()

            return prompt
        finally:
            VAR.reference = ""
            VAR.styling = ""

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
