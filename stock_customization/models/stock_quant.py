# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class StockQuant(models.Model):
	_inherit = 'stock.quant'
	
	condition_id = fields.Many2one(related='lot_id.condition_id', readonly=True)
	status_id = fields.Many2one(related='lot_id.status_id', readonly=True)
	length_stay = fields.Integer(related="lot_id.length_stay")

	def validate_no_duplicate_serial(self, vals):
		lot_id = vals.get('lot_id', False)
		query="""
			SELECT
				lot.name, lt.name
			FROM
				public.stock_quant as qt 
				JOIN public.stock_location as lt ON lt.id = qt.location_id
				JOIN public.product_product as pp ON pp.id = qt.product_id
				JOIN public.product_template as pt ON pt.id = pp.product_tmpl_id
				JOIN public.stock_production_lot as lot ON lot.id = qt.lot_id
			WHERE
				lt.usage = 'internal'
				and pt.tracking = 'serial'
				and qt.lot_id = '{}'
				and qt.company_id = '{}'
				and qt.quantity > 0
			;""".format(lot_id if lot_id else 0, self.env.company.id)
		self._cr.execute(query)
		result = self._cr.fetchall()
		compare = 2 if self.env.context.get('active_model', '') in ['stock.picking', 'stock.picking.type', 'mrp.production', 'helpdesk.delivery.wizard', 'helpdesk.return.wizard', 'helpdesk.ticket'] else 1
		if len(result) > compare:
			raise ValidationError(_("Los productos con seguimiento por serial sólo pueden tener 1 cantidad por empresa, usted está intentando añadir más.\nnúmeros de serie: {}".format(str(result[0][0]))))

	@api.model
	def create(self, vals):
		res = super(StockQuant, self).create(vals)
		if vals.get('quantity', 1) >= 0:
			self.validate_no_duplicate_serial(vals)
		return res
