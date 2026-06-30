**Name**
Delete.API

**Goal**
The goal of this skill is to provide a user-friendly way to delete one or all API files from a project's 'Apis' directory.

**Functionality**
This skill scans the `{project}/Apis` directory for existing API files. It then presents a selection list to the user, allowing them to choose a specific API to delete or to delete all detected APIs. The options include "All" (to delete everything) and "[Back]" (to cancel the operation). File deletion operations are reserved using `Patch.add()` before execution.

**Returns**
Returns `True` if the deletion process is successfully completed (either a single API or all APIs), or `False` if the user cancels the operation by selecting "[Back]". Returns an empty string if no API files are found in the project.