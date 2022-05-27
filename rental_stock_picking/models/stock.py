# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Location(models.Model):
	_inherit = "stock.location"
	
	rental_location = fields.Boolean('Is a Rental Location?', default=False, help='Check this box to allow using this location to put rental goods.')

class Warehouse(models.Model):
	_inherit = "stock.warehouse"
	
	rental_location_id = fields.Many2one('stock.location', string="Rental Location", check_company=True, help="The stock location used as destination when renting goods to this contact.")

class StockPicking(models.Model):
	_inherit = "stock.picking"

	@api.constrains('state')
	def _constrain_rental_validate(self):
		for rec in self:
			if rec.state == 'done':
				#Asigna el cliente y tipo de negociacion al lote cuando la ubicacion destino es de tipo Alquiler
				if rec.sale_id and rec.sale_id.is_rental_order and rec.location_dest_id.rental_location:
					lot_ids = rec.move_line_ids.mapped('lot_id').filtered(lambda l: l.product_id.product_type == '0')
					if lot_ids:
						lot_ids.update({
							'partner_id': rec.partner_id,
							'affiliated': rec.partner_id.affiliated,
							'negotiation_type_id': rec.sale_id.type_negotiation_id,
						})