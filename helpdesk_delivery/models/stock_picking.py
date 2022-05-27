# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Picking(models.Model):
	_inherit = "stock.picking"

	delivery_ticket_id = fields.Many2one('helpdesk.ticket', 'Ticket')

	def action_assign(self):
		res = super(Picking, self).action_assign()
		for rec in self:
			if rec.state == 'assigned' and rec.delivery_ticket_id and rec.move_line_ids:
				rec.delivery_ticket_id.lot_ids = rec.move_line_ids.mapped('lot_id').ids
		return res

	def button_validate(self):
		self.ensure_one()
		res = super(Picking, self).button_validate()
		if self.state == 'done' and self.delivery_ticket_id and self.move_line_ids:
			self.delivery_ticket_id.lot_ids = self.move_line_ids.mapped('lot_id').ids
		return res

	def incorporate_button(self):
		self.ensure_one()
		super(Picking, self).incorporate_button()
		if self.state == 'incorporated' and self.delivery_ticket_id and self.move_line_ids:
			self.delivery_ticket_id.lot_ids = self.move_line_ids.mapped('lot_id').ids