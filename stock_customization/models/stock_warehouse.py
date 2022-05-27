# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Warehouse(models.Model):
	_inherit = "stock.warehouse"

	code = fields.Char(size=11)
	region =fields.Many2one('crm.region', ondelete="restrict")
	kind_attention = fields.Selection([('1', 'Tradicional'), ('2', 'Evento')])
	event =fields.Many2one('event.name', ondelete="restrict")
	# warehouse_type = fields.Selection([
	# 	('central', _('Central warehouse')), 
	# 	('aux', _('Auxiliary warehouse')), 
	# 	('event', _('Event warehouse'))]
	# )