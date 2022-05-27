
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Repair(models.Model):
	_inherit = 'repair.order'

	lot_domain = fields.Many2many('stock.production.lot', string='Lot domain', compute="_compute_lot_domain", store=False)
	location_id = fields.Many2one(default=False)

	@api.depends('product_id', 'location_id')
	def _compute_lot_domain(self):
		for order in self:
			order.lot_domain = [(5, 0, 0)]
			if not order.ticket_id:
				order.lot_id = False
				if order.product_id and order.location_id and order.tracking in ['serial', 'lot']:
					quant = order.env['stock.quant'].search([('product_id','=', order.product_id.id), ('location_id','=',order.location_id.id)])
					if quant: order.lot_domain = quant.lot_id.ids

	@api.onchange('ticket_id', 'lot_id')
	def _onchange_ticket_id(self):
		if self.ticket_id and self.lot_id and self.lot_id.current_location:
			if self.lot_id.current_location.repair_location:
				self.location_id = self.lot_id.current_location
			else:
				return {
					'warning': {
						'title': _("Warning"),
						'message': _("""The customer's device is not in a repair location, you must select which location the repair is going to planned.""")
					}
				}