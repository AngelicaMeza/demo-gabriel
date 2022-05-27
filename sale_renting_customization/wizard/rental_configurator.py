# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class RentalWizard(models.TransientModel):
	_inherit = 'rental.wizard'

	@api.depends('product_id', 'warehouse_id')
	def _compute_rentable_lots(self):
		for rent in self:
			if rent.product_id and rent.tracking == 'serial':
				rentable_lots = self.env['stock.production.lot']._get_available_lots(rent.product_id, rent.warehouse_id.location_for_rental)
				domain = [
					('is_rental', '=', True),
					('product_id', '=', rent.product_id.id),
					('order_id.rental_status', 'in', ['pickup', 'return']),
					('state', 'in', ['sale', 'done']),
					('id', '!=', rent.rental_order_line_id.id)]
				if rent.warehouse_id:
					domain += [('order_id.warehouse_id', '=', rent.warehouse_id.id)]
				# Total of lots = lots available + lots currently picked-up.
				rentable_lots += self.env['sale.order.line'].search(domain).mapped('pickedup_lot_ids')
				rent.rentable_lot_ids = rentable_lots
			else:
				rent.rentable_lot_ids = self.env['stock.production.lot']