# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	company_pos_id = fields.Many2one(related="sale_id.company_pos_id", string="Operadora telefónica solicitada")
