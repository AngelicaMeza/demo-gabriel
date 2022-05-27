# -*- coding: utf-8 -*-

from odoo import api, fields, models


class BaseModuleUninstall(models.TransientModel):
	_inherit = "base.module.uninstall"

	def action_uninstall(self):
		modules = self.module_id
		##########################################################
		if modules.name == 'auditlog':
			rules =self.env['auditlog.rule'].search([])
			for rule in rules:
				rule.unsubscribe()
		##########################################################
		return modules.button_immediate_uninstall()