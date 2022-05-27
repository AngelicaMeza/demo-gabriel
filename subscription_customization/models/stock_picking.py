# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta

class Picking(models.Model):
	_inherit = "stock.picking"

	def button_validate(self):
		self.ensure_one()
		res = super(Picking, self).button_validate()

		for line in self.move_line_ids:
			if line.qty_done != 0:
				self.generate_subscriptions()
				break

		return res
	
	def generate_subscriptions(self):
		if self.sale_id:
			subscription_products = []
			for line in self.sale_id.order_line:
				if line.product_id.type == 'service' and line.product_id.recurring_invoice and not line.subscription_id:
					subscription_products.append(line)

		if self.picking_type_id.code == 'outgoing' and self.location_dest_id.usage == 'customer' and self.sale_id and 'optional_product_ids' in self.env['product.template']._fields and self.move_line_ids.mapped('product_id').mapped('optional_product_ids') and not self.sale_id.is_rental_order:
			to_create = dict()
			for line in self.move_line_ids:
				if line.product_id.optional_product_ids and line.qty_done != 0:
					for product in line.product_id.optional_product_ids:
						for subs in subscription_products:
							if subs.product_template_id.id == product.id:
								to_create[subs] = line.lot_id
								subscription_products.remove(subs)
								break
			
			self.sale_id.create_subscriptions2(to_create)

class production_lot_inherit(models.Model):
	_inherit = 'stock.production.lot'

	subscription_id = fields.Many2one('sale.subscription')

class StockImmediateTransfer(models.TransientModel):
	_inherit = 'stock.immediate.transfer'

	def process(self):
		res = super(StockImmediateTransfer, self).process()
		if self.pick_ids.picking_type_id.code == 'outgoing' and self.pick_ids.location_dest_id.usage == 'customer' and self.pick_ids.sale_id and 'optional_product_ids' in self.env['product.template']._fields and self.pick_ids.move_line_ids.mapped('product_id').mapped('optional_product_ids') and not self.pick_ids.sale_id.is_rental_order:
			self.pick_ids.generate_subscriptions()
		
		return res
