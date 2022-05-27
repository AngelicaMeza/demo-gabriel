# -*- coding: utf-8 -*-

from odoo import models, fields

class AccountMove(models.Model):
	_inherit = "account.move"

	def button_cancel(self):
		for line in self.invoice_line_ids:
			if line.lot_id and line.lot_id.invoiced:
				line.lot_id.invoiced = False
		super(AccountMove, self).button_cancel()

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	lot_id = fields.Many2one('stock.production.lot', string='Lotes/Números de serie', readonly=True)

	def unlink(self):
		self.lot_id.sudo().write({'invoiced': False})
		res = super(AccountMoveLine, self).unlink()
		return res