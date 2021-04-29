
import frappe
from frappe.core.page.background_jobs.background_jobs import get_info

def get_context(context):

	color_map = {
		'Processing': 'blue',
		'Under Review': 'pink',
		'Rejected': 'red',
		'Approved': 'green',
		'Unapproved': 'red',
		
	}

	context.contributions = []
	contributions = frappe.get_list("Pull Request", ["pr_link", "status", "name"])
	for contribution in contributions:
		contribution.files_edited = frappe.get_all(
			"Files Changed",
			fields=["web_route"],
			filters=[["pull_request", "=", contribution.name]],
		)
		contribution.files_edited = [i.web_route for i in contribution.files_edited ]
		files_edited = []
		for i in contribution.files_edited:
			if i.endswith('/'):
				files_edited.append(i.split('/')[-2])
			else:
				files_edited.append(i.split('/')[-1])
		contribution.color = color_map[contribution.status]

		contribution.files_edited = f"{', '.join( files_edited )} </ol>"
		context.contributions.extend([contribution])
	print(contribution)
	return context