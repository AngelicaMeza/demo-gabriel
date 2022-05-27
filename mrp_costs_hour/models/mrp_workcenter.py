# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MrpWorkcenter(models.Model):
	_inherit = "mrp.workcenter"

	#cost per hour currency
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)