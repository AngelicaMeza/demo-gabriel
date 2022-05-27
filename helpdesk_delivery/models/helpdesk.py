# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HelpdeskTeam(models.Model):
	_inherit = "helpdesk.team"
	
	use_delivery = fields.Boolean('Deliveries')
	use_return = fields.Boolean('Returns')

class HelpdeskTicket(models.Model):
	_inherit = 'helpdesk.ticket'

	#delivery
	delivery_pickings_count = fields.Integer('Deliver Orders Count', compute="_compute_delivery_pickings_count")
	delivery_picking_ids = fields.One2many('stock.picking', 'delivery_ticket_id', string="Delivery Orders")
	use_delivery = fields.Boolean(related='team_id.use_delivery')
	lot_ids = fields.Many2many('stock.production.lot', 'delivery_lots', 'id', string='Equipo a instalar', readonly=True)

	#return
	return_pickings_count = fields.Integer('Return Orders Count', compute="_compute_return_pickings_count")
	return_picking_ids = fields.Many2many('stock.picking', 'return_table', 'id', string="Return Orders")
	use_return = fields.Boolean(related='team_id.use_return')

	@api.depends('delivery_picking_ids')
	def _compute_delivery_pickings_count(self):
		"""Actualiza el numero de entregas que pertenecen al ticket"""
		for ticket in self:
			ticket.delivery_pickings_count = len(ticket.delivery_picking_ids)

	@api.depends('return_picking_ids')
	def _compute_return_pickings_count(self):
		"""Actualiza el numero de devoluciones que pertenecen al ticket"""
		for ticket in self:
			ticket.return_pickings_count = len(ticket.return_picking_ids)

	def deliver_products(self):
		if self.product_lot:
			return {
				'type': 'ir.actions.act_window',
				'name': _('Plan Delivery'),
				'res_model': 'helpdesk.delivery.wizard',
				'view_mode': 'form',
				'target': 'new',
				'context': {
					'default_ticket_id': self.id,
					'default_company_id': self.company_id.id,
					'default_lot_id': self.product_lot.id,
				}
			}
		else:
			raise ValidationError(_("""There is not device to manager."""))

	def return_products(self):
		if self.product_lot:
			return {
				'type': 'ir.actions.act_window',
				'name': _('Plan Return'),
				'res_model': 'helpdesk.return.wizard',
				'view_mode': 'form',
				'target': 'new',
				'context': {
					'default_ticket_id': self.id,
					'default_company_id': self.company_id.id,
					'default_lot_id': self.product_lot.id,
				}
			}
		else:
			raise ValidationError(_("""There is not device to manager."""))

	def action_view_deliveries(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Delivery Orders'),
			'res_model': 'stock.picking',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', self.delivery_picking_ids.ids)],
			'context': dict(self._context, create=False, default_company_id=self.company_id.id)
		}
	
	def action_view_returns(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Return Orders'),
			'res_model': 'stock.picking',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', self.return_picking_ids.ids)],
			'context': dict(self._context, create=False, default_company_id=self.company_id.id)
		}

	def action_generate_fsm_task(self):
		self.ensure_one()
		res = super(HelpdeskTicket, self).action_generate_fsm_task()
		res['context'].update({'default_lot_ids': self.lot_ids.ids})
		return res