# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.router import resolve_route
from frappe import _
import os
import shutil
import re
import json
import subprocess
from github import Github
from edit_docs.www.edit import  get_source_generator, get_path_without_slash


class PullRequest(WebsiteGenerator):
	def validate(self):
		self.set_route()

	def raise_pr(self):
		self.set_vars()
		self.setup_repo()
		self.load_attachments()
		self.save_files()
		self.save_attachments()
		self.git_set_remotes()
		self.git_push()
		self._raise_pr()
		self.cleanup()

	def setup_repo(self):
		shutil.copytree(
			"/".join(frappe.get_app_path(self.app).split("/")[:-1]),
			f"{self.repository_base_path}/",
		)

	def set_vars(self):
		self.jenv = frappe.get_jenv()
		repository = frappe.get_all("Repository", [["enabled","=","1"]])
		if not repository:
			frappe.throw("No active repositories found, contact System Manager")
		self.app = repository[0]["name"]
		self.repository = frappe.get_doc("Repository", self.app)
		self.uuid = frappe.generate_hash()
		self.repository_base_path = f"{os.getcwd()}/{frappe.local.site}/private/edit_docs/{self.uuid}"

	def save_files(self):
		edits = frappe.get_all(
			"Files Changed",
			filters=[["pull_request", "=", self.name]],
			fields=["name", "new_code", "web_route", "new"],
		)

		for edit in edits:
			self.save_file(edit)

	def save_file(self, edit):
		if edit.new:
			path = f"{self.repository_base_path}/{self.app}/www{edit.web_route}.md"
		else:
			resolved_route = resolve_route(get_path_without_slash(edit.web_route))
			if resolved_route.page_or_generator == "Generator":
				path = f"{self.repository_base_path}/{path}"

			elif resolved_route.page_or_generator == "Page":
				path = f"{self.repository_base_path}/{self.app}/{resolved_route.template}"

		self.update_file(path, edit.new_code)

	def save_attachments(self):
		for attachment in self.attachments:
			if attachment.get("save_path"):
				shutil.copy(
					f'{os.getcwd()}/{frappe.local.site}/public{attachment.get("file_url")}',
					f'{self.repository_base_path}/{self.app}/www{attachment.get("save_path").replace("{{docs_base_url}}", "/docs")}',
				)

	def _raise_pr(self,):
		g = Github(self.repository.get_password("token"))

		upstream_repo = g.get_repo("/".join(self.repository.upstream.split("/")[3:5]))

		try:
			upstream_pullrequest = upstream_repo.create_pull(
				self.pr_title,
				self.pr_body,
				self.repository.branch,
				"{}:{}".format(self.repository.origin.split("/")[3], self.uuid),
				True,
			)
		except Exception:
			frappe.throw(
				frappe.get_traceback(), title=_(f"Please recheck the Repository origin: {self.repository.origin}")
			)

		upstream = self.repository.upstream.replace(".git", "/")
		self.pr_link = f"{upstream}/pull/{upstream_pullrequest.number}"
		self.repository = self.app
		self.save()

	def cleanup(self):
		try:
			shutil.rmtree(self.repository_base_path)
		except:
			frappe.msgprint("Error while deleting directory")

	def update_file(self, path, code):
		f = open(path, "w")
		f.write(code)
		f.close()

	def load_attachments(self):
		self.attachments = json.loads(self.attachment_path_mapping)

	def git_set_remotes(self):
		popen(f"git -C {self.repository_base_path} remote rm upstream ")
		popen(f"git -C {self.repository_base_path} remote rm origin ")
		popen(
			f"git -C {self.repository_base_path} remote add origin {self.repository.origin}", raise_err=True
		)
		popen(
			f"git -C {self.repository_base_path} remote add upstream {self.repository.upstream}", raise_err=True
		)

	def git_push(self):
		popen(f"git -C {self.repository_base_path} branch {self.uuid}", raise_err=True)
		popen(f"git -C {self.repository_base_path} checkout {self.uuid}", raise_err=True)
		popen(f"git -C {self.repository_base_path} add .", raise_err=True)
		email = frappe.session.user
		name = frappe.db.get_value("User", frappe.session.user, ["first_name"], as_dict=True).get("first_name")
		popen(f'git -C {self.repository_base_path} commit -m "{self.pr_title}\n\n\n\nCo-authored-by: {name} <{email}>" ', raise_err=True)
		popen(f'git -C {self.repository_base_path} push origin {self.uuid}', raise_err=True)

def update_pr_status():
	repository = frappe.get_doc("Repository", "erpnext_documentation")
	g = Github(repository.get_password("token"))

	try:
		repo = g.get_repo("/".join(repository.upstream.split("/")[3:5]))
	except Exception:
		frappe.throw(
			frappe.get_traceback(), title=_(f"Please recheck the Repository upstream: {repository.upstream}")
		)

	for pr in frappe.db.get_all("Pull Request", fields=["name", "pr_link"]):
		if pr.pr_link:
			gh_pr = repo.get_pull(int(pr.pr_link.split("/")[-1]))
			status = "Approved" if gh_pr.merged else "Unapproved"
			frappe.db.update("Pull Request", pr.name, "status", status)
	frappe.db.commit()


def popen(command, *args, **kwargs):
	output = kwargs.get('output', True)
	cwd = kwargs.get('cwd')
	shell = kwargs.get('shell', True)
	raise_err = kwargs.get('raise_err')
	env = kwargs.get('env')
	if env:
		env = dict(environ, **env)

	proc = subprocess.Popen(command,
		stdout=None if output else subprocess.PIPE,
		stderr=None if output else subprocess.PIPE,
		shell=shell,
		cwd=cwd,
		env=env
	)

	outs, errs = proc.communicate()

	if proc.returncode and raise_err:
		frappe.throw(
				errs, title=_(command)
			)

	return (outs, errs)