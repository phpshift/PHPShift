**Name**
Delete.Page

**Goal**
To provide an interactive tool for users to delete existing pages (folders) from the project's 'Pages' directory.

**Functionality**
This skill scans the `{project}/Pages` directory to identify all subfolders, which represent individual pages. It then presents these pages to the user as a selectable list. The user is given options to either delete "All" available pages, select a specific page for deletion, or "[Back]" out of the operation. Upon selection and explicit confirmation, the chosen page(s) and all their contents will be permanently removed from the file system.

**Returns**
`True` if a page or multiple pages were successfully deleted.
`False` if the operation was cancelled by the user, if no pages were found to delete, or if an error occurred during deletion.