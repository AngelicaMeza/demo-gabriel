# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CheckPointLine(models.Model):
	_name = "check.point.line"
	_description = "check point line"
	_order = "sequence"

	sequence = fields.Integer()
	name = fields.Char()
	check_yes = fields.Boolean()
	check_no = fields.Boolean()
	description = fields.Text()

class QualityPoint(models.Model):
	_inherit = "quality.point"
	_description = "quality point line"

	check_list_format = fields.Many2one('check.list', ondelete="restrict")

	check_point_line = fields.Many2many('check.point.line')
	
	# set check list
	@api.onchange('check_list_format')
	def _set_check_list(self):
		if self.check_list_format:
			aux_checks = []
			self.check_point_line = [(5, 0, 0)]
			for check in self.check_list_format.check_points:
				aux_checks.append((0, 0, {
						'sequence': check.sequence, 
						'name': check.name,
						'check_yes': False,
						'check_no': False,
						'description': False
					}))
			self.check_point_line = aux_checks