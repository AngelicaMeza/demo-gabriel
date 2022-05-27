# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _

class ProductProduct(models.Model):
	_inherit = 'product.product'

	def _compute_bom_price(self, bom, boms_to_recompute=False):
		self.ensure_one()
		if not bom:
			return self.standard_price
		if not boms_to_recompute:
			boms_to_recompute = []
		total = 0
		for opt in bom.routing_id.operation_ids:
			duration_expected = (
				opt.workcenter_id.time_start +
				opt.workcenter_id.time_stop +
				opt.time_cycle)
			wc = opt.workcenter_id
			total += (duration_expected / 60) * wc.currency_id._convert(wc.costs_hour, wc.company_id.currency_id, wc.company_id, fields.datetime.today())
		for line in bom.bom_line_ids:
			if line._skip_bom_line(self):
				continue

			# Compute recursive if line has `child_line_ids`
			if line.child_bom_id and line.child_bom_id in boms_to_recompute:
				child_total = line.product_id._compute_bom_price(line.child_bom_id, boms_to_recompute=boms_to_recompute)
				total += line.product_id.uom_id._compute_price(child_total, line.product_uom_id) * line.product_qty
			else:
				total += line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line.product_qty
		return bom.product_uom_id._compute_price(total / bom.product_qty, self.uom_id)
