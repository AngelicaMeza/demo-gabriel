# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lib2to3.pgen2.pgen import DFAState
from odoo import api, fields, models, _

class Warehouse(models.Model):
	_inherit = "stock.warehouse"

	project_id = fields.Many2one('project.project', string='Project')

class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	use_fsm = fields.Boolean('Can it plan interventions?')
	project_id = fields.Many2one('project.project', related='warehouse_id.project_id', readonly=True)
	task_type_id = fields.Many2one('fsm.task.type', string='Task type', ondelete="restrict")

class Picking(models.Model):
	_inherit = "stock.picking"

	use_fsm = fields.Boolean(related='picking_type_id.use_fsm')
	fsm_task_ids = fields.One2many('project.task', 'picking_id', string='Tasks', domain=[('is_fsm', '=', True)], copy=False)
	fsm_task_count = fields.Integer(compute='_compute_fsm_task_count')
	task_stage = fields.Many2one('project.task.type', string='Task stage', compute='_compute_calculate_task_stage', store=True)
	show_intervention = fields.Boolean(compute='_compute_show_intervention')

	@api.depends('move_line_ids_without_package')
	def _compute_show_intervention(self):
		router_or_accesory = any([line.product_id.product_type in ['1', '2'] for line in self.move_line_ids_without_package])
		pos = any([line.product_id.product_type == '0' for line in self.move_line_ids_without_package])
		if ( router_or_accesory and not pos and self.state in ['assigned', 'done']) or\
			( pos and self.state in ['incorporated', 'done']):
			self.show_intervention = True
		else:
			self.show_intervention = False

	@api.depends('fsm_task_ids', 'fsm_task_ids.stage_id')
	def _compute_calculate_task_stage(self):
		"""Calculate the last task stage"""
		for picking in self: 
			if picking.fsm_task_ids:
				picking.task_stage = picking.fsm_task_ids.sorted(key=lambda l: l.create_date)[-1].stage_id.id
			elif not picking.task_stage.is_closed:
				picking.task_stage = False

	@api.depends('fsm_task_ids')
	def _compute_fsm_task_count(self):
		for picking in self:
			picking.fsm_task_count = len(picking.fsm_task_ids)

	def action_view_fsm_tasks(self):
		fsm_form_view = self.env.ref('industry_fsm.project_task_view_form')
		fsm_list_view = self.env.ref('industry_fsm.project_task_view_list_fsm')
		return {
			'type': 'ir.actions.act_window',
			'name': _('Tasks from Tickets'),
			'res_model': 'project.task',
			'domain': [('id', 'in', self.fsm_task_ids.ids)],
			'views': [(fsm_list_view.id, 'tree'), (fsm_form_view.id, 'form')],
		}

	def action_generate_fsm_task(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Create a Field Service task'),
			'res_model': 'stock.create.fsm.task',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_picking_id': self.id,
				'default_region_id': self.picking_type_id.warehouse_id.region.id or self.partner_id.region_id.id,
				'default_partner_id': self.partner_id.id or False,
				'default_name': self.picking_type_id.task_type_id.name,
				'default_project_id': self.picking_type_id.project_id.id,
				'default_task_type_id': self.picking_type_id.task_type_id.id,
			}
		}
