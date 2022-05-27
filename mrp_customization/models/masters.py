# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ApplicationVersions(models.Model):
	_name = "application.versions"

	name = fields.Char(string='Nombre', required=True)
	brand_ids = fields.Many2many('brand.stock', string='Marcas', ondelete="restrict")
	product_ids = fields.Many2many('product.product', string='Productos')
	active = fields.Boolean('Active', default=True)