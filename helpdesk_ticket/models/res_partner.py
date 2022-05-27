# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Partner(models.Model):
	_inherit = "res.partner"

	def name_get(self):
		result = []
		for rec in self:
			name = rec.name
			if rec.affiliated:
				name += " - " + rec.affiliated
			result.append((rec.id, name))
		return result