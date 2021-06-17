# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from ghdiff import diff
from frappe.website.router import resolve_route


class WebPageUpdateRequest(WebsiteGenerator):

	def validate(self):
		jenv = frappe.get_jenv()
		route = resolve_route(self.web_route[1:])
		if route.page_or_generator == "Generator":
			code = route.doc.content
		elif route.page_or_generator == "Page":
			source = jenv.loader.get_source(jenv, route.template)[0]
			code = source
		self.orignal_code = code
		self.diff = diff(code, self.new_code)
		route = resolve_route(self.web_route[1:])
		route.docs_base_url = '/docs'
		old_html= frappe.utils.md_to_html(self.orignal_code)
		new_html= frappe.utils.md_to_html(self.new_code)
		self.orignal_preview_store = jenv.from_string(old_html, route)
		self.orignal_preview_store = self.orignal_preview_store.render()
		self.new_preview_store = jenv.from_string(new_html, route)
		self.new_preview_store = self.new_preview_store.render()
		self.set_route()
