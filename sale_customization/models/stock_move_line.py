# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	company_pos_id = fields.Many2one(related="lot_id.network_operator_id", string="Operadora")