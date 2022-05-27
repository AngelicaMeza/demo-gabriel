# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ValidateActive(models.TransientModel):
    _name = 'account.asset.validate'
    _description = 'Validate active'

    def do_action(self):
        active = self.env['account.asset'].browse(self._context.get('active_ids', []))
        for record in active:
            if record.state == 'draft':
                record.validate()