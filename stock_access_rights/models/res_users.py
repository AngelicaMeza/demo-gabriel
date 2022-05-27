# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Users(models.Model):
	_inherit = "res.users"

	user_line_ids = fields.One2many('stock.warehouse.user.line', 'user_id', string='Operations', readonly=True)