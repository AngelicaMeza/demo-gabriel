# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	brand_id = fields.Many2one('brand.stock', string="Brand", ondelete="restrict")
	communication_id = fields.Many2many('crm.point.sale', string="Communication", ondelete="restrict")
	network_operator_id = fields.Many2one('crm.company.pos', string='Operadora', ondelete="restrict")
	product_type = fields.Selection([
		('0', 'POS'),
		('1', 'Router'),
		('2', 'Accesorio'),
		('3', 'Simcard'),
		('4', _('N/A')), 
		('5', 'Llave')],
		string='Tipo',
		default='4'
	)