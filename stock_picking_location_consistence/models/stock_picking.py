# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	@api.onchange('location_id')
	def set_line_location(self):
		self.move_line_ids_without_package.write({'location_id': self.location_id.id})
	
	@api.onchange('location_dest_id')
	def set_line_dest_location(self):
		self.move_line_ids_without_package.write({'location_dest_id': self.location_dest_id.id})