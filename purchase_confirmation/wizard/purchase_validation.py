	# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class purchaseValidation(models.TransientModel):
    _name = "purchase.valdation"

    purchase_number = fields.Integer()
    conf_num = fields.Integer()

    def wizard_confirm(self):
        purchase_order = self.env['purchase.order'].browse(self.env.context['purchase_id'])
        purchase_order.state = 'fin_approve'