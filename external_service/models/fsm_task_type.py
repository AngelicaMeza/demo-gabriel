# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class TaskTypeLine(models.Model):
	_name = "fsm.task.type.line"
	_description = "Task type lines"

	hours = fields.Integer('Hours')
	cluster_ids = fields.Many2many('segmentation.cluster', string='Cluster(s)', ondelete="restrict")
	task_type = fields.Many2one('fsm.task.type', string='Task type')


class TaskType(models.Model):
	_name = "fsm.task.type"
	_description = "Task types"

	name = fields.Char('Description', required=True)
	code = fields.Integer('Code', required=True)
	time_ids = fields.One2many('fsm.task.type.line', 'task_type', string='Times', required=True)
	cluster_domain = fields.Many2many('segmentation.cluster', string='Cluster(s)', ondelete="restrict")
	active = fields.Boolean('Active', default=True)

	@api.onchange('time_ids')
	def _onchange_cluster_domain(self):
		self.cluster_domain = [(5, 0, 0)]
		if self.time_ids:
			self.cluster_domain = self.time_ids.mapped('cluster_ids').ids

	@api.constrains('time_ids')
	def _constrains_no_empty_lines(self):
		for line in self.time_ids:
			if not line.cluster_ids:
				raise ValidationError(_("""There are empty lines, please erase them or include any cluster !!!"""))

	@api.model_create_multi
	def create(self, vals_list):
		res = super(TaskType, self).create(vals_list)
		for rec in res:
			rec.code = self.env['ir.sequence'].next_by_code('fsm.task.type')
		return res

	_sql_constraints = [
		('name_code_uniq', 'unique (name, code)', "Task type already exist !!!"),
	]