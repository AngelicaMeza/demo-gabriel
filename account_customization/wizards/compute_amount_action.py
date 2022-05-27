# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ComputeAmountAction(models.TransientModel):
    _name = 'account.compute.amounts.action'
    _description = 'Recompute all the amounts'

    def do_action(self):
        active = self.env['account.move'].browse(self._context.get('active_ids', []))
        for record in active:
            if record.state != 'cancel':
                record._compute_amount()