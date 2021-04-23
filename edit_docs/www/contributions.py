
import frappe
from frappe.core.page.background_jobs.background_jobs import get_info

def get_context(context):
	context.contributions = []
	contributions = frappe.get_list("Pull Request", ["pr_link", "status", "name"])
	for contribution in contributions:
		contribution.files_edited = frappe.get_all(
			"Files Changed",
			fields=["web_route"],
			filters=[["pull_request", "=", contribution.name]],
		)

		contribution.files_edited = f"<ol><li> {'<li>'.join( [i.web_route for i in contribution.files_edited ])} </ol>"
		context.contributions.extend([contribution])
	context.currently_running = len([d.get("job_name") for d in get_info() if d.get("job_name")==f"Pull-Request-{frappe.session.user}"]) or 0
	return context