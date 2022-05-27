# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResCompany(models.Model):
	_inherit = "res.company"

	sent_purchase_order_count = fields.Integer(default=0)


class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"

	sent_purchase_order = fields.Boolean('Cantidad mínima de presupuestos', config_parameter='purchase_requisition.sent_purchase_order')
	sent_purchase_order_count = fields.Integer(related='company_id.sent_purchase_order_count', string='Limite', readonly=False)