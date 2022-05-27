# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.mrp_account.models.mrp_production import MrpProduction

def _cal_price(self, consumed_moves):
	"""Set a price unit on the finished move according to `consumed_moves`.
	"""
	super(MrpProduction, self)._cal_price(consumed_moves)
	work_center_cost = 0
	finished_move = self.move_finished_ids.filtered(lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
	if finished_move:
		finished_move.ensure_one()
		for work_order in self.workorder_ids:
			time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
			duration = sum(time_lines.mapped('duration'))
			time_lines.write({'cost_already_recorded': True})
			wc = work_order.workcenter_id
			work_center_cost += (duration / 60.0) * wc.currency_id._convert(wc.costs_hour, wc.company_id.currency_id, wc.company_id, fields.datetime.today())
		if finished_move.product_id.cost_method in ('fifo', 'average'):
			qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
			extra_cost = self.extra_cost * qty_done
			finished_move.price_unit = (sum([-m.stock_valuation_layer_ids.value for m in consumed_moves.sudo()]) + work_center_cost + extra_cost) / qty_done
	return True

MrpProduction._cal_price = _cal_price

class MrpProductionCostsHour(models.Model):
	_inherit = 'mrp.production'

	def _prepare_wc_analytic_line(self, wc_line):
		wc = wc_line.workcenter_id
		hours = wc_line.duration / 60.0
		value = hours * wc.currency_id._convert(wc.costs_hour, wc.company_id.currency_id, wc.company_id, fields.datetime.today())
		account = wc.costs_hour_account_id.id
		return {
			'name': wc_line.name + ' (H)',
			'amount': -value,
			'account_id': account,
			'ref': wc.code,
			'unit_amount': hours,
			'company_id': self.company_id.id,
		}