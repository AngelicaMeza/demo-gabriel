# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    def _prepare_default_values(self, move):
        res = super(AccountDebitNote, self)._prepare_default_values(move)
        if move.partner_id:
            res['partner_id'] = move.partner_id.id
        return res