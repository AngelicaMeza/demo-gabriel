# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProjectTaskType(models.Model):
	_inherit = 'project.task.type'

	failed_stage = fields.Boolean()

class ProjectProject(models.Model):
	_inherit = "project.project"

	region_id = fields.Many2one('crm.region', string='Región', ondelete="restrict")
	assigned_to = fields.Many2one('res.users')

class Task(models.Model):
	_inherit = 'project.task'

	picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
	failure_stage = fields.Boolean(related='stage_id.failed_stage')
	create_in_failure = fields.Boolean()

	def action_view_picking(self):
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'stock.picking',
			'view_mode': 'form',
			'res_id': self.picking_id.id,
		}
	
	@api.constrains('project_id')
	def project_user_c(self):
		if self.project_id and self.project_id.assigned_to:
			self.user_id = self.project_id.assigned_to
		else:
			self.user_id = False

	@api.onchange('project_id')
	def project_user_o(self):
		if self.project_id and self.project_id.assigned_to:
			self.user_id = self.project_id.assigned_to
		else:
			self.user_id = False

	@api.model
	def create(self, vals):
		if vals.get('stage_id', False):
			stage = self.env['project.task.type'].browse(vals['stage_id'])
			if stage.sequence == 0 and stage.failed_stage:
				vals['create_in_failure'] = True
		else:
			vals['create_in_failure'] = True
			
		return super(Task, self).create(vals)

	def mark_as_faild(self):
		next_fail_stage = self.env['project.task.type'].search([('failed_stage', '=', True), ('sequence', '>', self.stage_id.sequence)], order='sequence asc')
		found = False
		for project in next_fail_stage:
			if self.project_id in project.project_ids:
				self.stage_id = project
				self.create_in_failure = False
				found = True
				break
		else:
			raise ValidationError (_("no failed stage is configured"))
		if not found:
			raise ValidationError(_("no failed stage is configured for this project"))

	def action_fsm_validate(self):
		result = super(Task, self).action_fsm_validate()
		self.create_in_failure = False
		return result