# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, models, fields, _

class StockCreateTask(models.TransientModel):
	_name = 'stock.create.fsm.task'
	_description = 'Create a Field Service task'

	picking_id = fields.Many2one('stock.picking', string='Related picking', required=True)
	company_id = fields.Many2one(related='picking_id.company_id')
	region_id = fields.Many2one('crm.region', 'Region', ondelete="restrict")
	
	name = fields.Char('Title', required=True)
	partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
	project_id = fields.Many2one('project.project', string='Project', required=True)
	task_type_id = fields.Many2one('fsm.task.type', string='Task type', required=True)
	edit_proyect = fields.Boolean()
	edit_task_type = fields.Boolean()

	@api.model
	def default_get(self, fields):
		values = super(StockCreateTask, self).default_get(fields)
		if not values.get('project_id', False):
			values['edit_proyect'] = True
		if not values.get('task_type_id', False):
			values['edit_task_type'] = True
		return values

	def action_generate_task(self):
		self.ensure_one()
		planned_date_begin = planned_date_end = False
		task_type_line = self.picking_id.picking_type_id.task_type_id.time_ids.filtered(lambda l: self.partner_id.cluster_id in l.cluster_ids)

		if task_type_line:
			planned_date_begin = planned_date_end = fields.Datetime.now()
			working_calendar = self.env.company.resource_calendar_id
			avg_hour = working_calendar.hours_per_day
			
			days = task_type_line.hours // avg_hour
			hours = task_type_line.hours % avg_hour

			if days > 0:
				planned_date_end = working_calendar.plan_days(days + 1, planned_date_end, compute_leaves=True)
				planned_date_end = planned_date_end.replace(
					hour=planned_date_begin.hour,
					minute=planned_date_begin.minute,
					second=planned_date_begin.second,
					microsecond=planned_date_begin.microsecond
				)
			
			planned_date_end = working_calendar.plan_hours(hours, planned_date_end, compute_leaves=True)

		new_task = self.env['project.task'].create({
			'partner_id': self.partner_id.id,
			'name': self.name,
			'project_id': self.project_id.id,
			'task_type_id': self.task_type_id.id,
			'planned_date_begin': planned_date_begin,
			'planned_date_end': planned_date_end,
			'lot_ids': self.picking_id.move_line_ids_without_package.mapped('lot_id').ids,
			'task_origin': self.picking_id.name or False
		})

		self.picking_id.fsm_task_ids |= new_task

		return {
			'type': 'ir.actions.act_window',
			'name': _('Create a Field Service task'),
			'res_model': 'project.task',
			'res_id': new_task.id,
			'view_mode': 'form',
			'view_id': self.env.ref('industry_fsm.project_task_view_form').id,
			'context': {'fsm_mode': True}
		}

class CreateTask(models.TransientModel):
	_inherit = 'helpdesk.create.fsm.task'

	region_id = fields.Many2one('crm.region', related='partner_id.region_id')
	task_type_id = fields.Many2one('fsm.task.type', string='Task type')
	edit_task_type = fields.Boolean()

	@api.onchange('helpdesk_ticket_id')
	def _default_task_type(self):
		"""Set task_type_id to default in helpdesk requirement"""
		if self.helpdesk_ticket_id and self.helpdesk_ticket_id.ticket_type_id.task_type_id:
			self.task_type_id = self.helpdesk_ticket_id.ticket_type_id.task_type_id
			self.edit_task_type = False
		else:
			self.edit_task_type = True

	@api.onchange('helpdesk_ticket_id')
	def _default_project_id(self):
		if self.helpdesk_ticket_id:

			picking_list = self.helpdesk_ticket_id.delivery_picking_ids.ids + self.helpdesk_ticket_id.return_picking_ids.ids
			picking_id = self.env['stock.picking'].search([('id','in',picking_list),('state','in',['assigned','incorporated','done'])], order='create_date desc', limit=1) if picking_list else False

			if picking_id:
				self.project_id = picking_id.picking_type_id.warehouse_id.project_id.id
			
			elif self.helpdesk_ticket_id.product_lot and self.helpdesk_ticket_id.product_lot.move_id:
				self.project_id = self.helpdesk_ticket_id.product_lot.move_id.warehouse_id.project_id.id
			
			else:
				project_ids = self.env['project.project'].search([('company_id','=', self.company_id.id), ('is_fsm', '=', True), ('region_id','=', self.region_id.id)])
				if len(project_ids) == 1: self.project_id = project_ids

	def action_generate_task(self):
		self.ensure_one()
		values = self._prepare_values()
		new_task = self.env['project.task'].create(self._convert_to_write(values))

		#add origin ticket name
		if self.helpdesk_ticket_id:
			new_task.write({'task_origin': 'Ticket #%s' % self.helpdesk_ticket_id.id})

		#add task type and calculate its hours
		if self.task_type_id:
			task_type_line = self.task_type_id.time_ids.filtered(lambda l: self.partner_id.cluster_id in l.cluster_ids)
			if task_type_line:
				planned_date_begin = planned_date_end = fields.Datetime.now()
				working_calendar = self.env.company.resource_calendar_id
				avg_hour = working_calendar.hours_per_day
				
				days = task_type_line.hours // avg_hour
				hours = task_type_line.hours % avg_hour

				if days > 0:
					planned_date_end = working_calendar.plan_days(days + 1, planned_date_end, compute_leaves=True)
					planned_date_end = planned_date_end.replace(
						hour=planned_date_begin.hour,
						minute=planned_date_begin.minute,
						second=planned_date_begin.second,
						microsecond=planned_date_begin.microsecond
					)
				
				planned_date_end = working_calendar.plan_hours(hours, planned_date_end, compute_leaves=True)

				new_task.write({
					'task_type_id': self.task_type_id.id,
					'planned_date_begin': planned_date_begin,
					'planned_date_end': planned_date_end,
				})

		#add lots to deliver from helpdesk
		if self.helpdesk_ticket_id.lot_ids:
			new_task.write({
				'lot_ids': self.helpdesk_ticket_id.lot_ids.ids,
			})

		return new_task