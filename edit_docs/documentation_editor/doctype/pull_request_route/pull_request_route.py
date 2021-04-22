# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

# import frappe
from frappe.model.document import Document
import frappe
from ghdiff import diff
from frappe.website.router import resolve_route
import re
from frappe.website.context import build_context
from edit_docs.www.edit import clean_js_css, get_source_generator, get_path_without_slash


class PullRequestRoute(Document):
	def validate(self):
		jenv = frappe.get_jenv()
		try:
			route = resolve_route(get_path_without_slash(self.web_route))
		except Exception:
			frappe.throw(
				frappe.get_traceback(), title=_(f"Please recheck the path: {self.web_route}")
			)
		if not route:
			self.validate_new_file()
			return

		route.route = get_path_without_slash(self.web_route)
		route.path = route.route
		route = build_context(route)

		if route.page_or_generator == "Generator":
			self.orignal_code = get_source_generator(route, jenv)
			self.orignal_preview_store = self.orignal_code
			self.new_preview_store = self.new_code

		elif route.page_or_generator == "Page":
			self.orignal_code = jenv.loader.get_source(jenv, route.template)[0]
			old_html = self.orignal_code
			new_html = self.new_code
			if route.template.endswith(".md"):
				old_html = frappe.utils.md_to_html(self.orignal_code)
				new_html = frappe.utils.md_to_html(self.new_code)

			self.orignal_preview_store = clean_js_css(route, old_html,  jenv)
			self.new_preview_store = clean_js_css(route, old_html, jenv)

		self.set_diff()

	def validate_new_file(self):
		self.orignal_code = ""
		self.diff = diff(self.orignal_code, self.new_code)
		old_html = frappe.utils.md_to_html(self.orignal_code)
		new_html = frappe.utils.md_to_html(self.new_code)
		self.new = 1
		self.orignal_preview_store = ""
		self.new_preview_store = new_html

	def set_diff(self):
		self.diff = diff(self.orignal_code, self.new_code)
