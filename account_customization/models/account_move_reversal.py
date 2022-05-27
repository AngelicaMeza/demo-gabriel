# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res['partner_id'] = move.partner_id.id
        return res