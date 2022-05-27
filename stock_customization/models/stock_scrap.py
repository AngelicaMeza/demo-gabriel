# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockScrap(models.Model):
	_inherit = 'stock.scrap'

	lot_domain = fields.Many2many('stock.production.lot', string='Lot domain')

	@api.onchange('picking_id', 'product_id')
	def _set_lot_domain(self):
		self.lot_domain = [(5, 0, 0)]
		if self.picking_id and self.picking_id.move_line_ids and self.product_id and self.tracking != 'none':
			moves = self.picking_id.move_line_ids.filtered(lambda m: m.product_id == self.product_id)
			self.lot_domain = moves.lot_id