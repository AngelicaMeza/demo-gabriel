# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CalculateAmortization(models.TransientModel):
    _name = 'account.asset.amortization'
    _description = 'calculate amortization'

    def do_action(self):
        active = self.env['account.asset'].browse(self._context.get('active_ids', []))
        for record in active:
            if record.state == 'draft':
                record.compute_depreciation_board()