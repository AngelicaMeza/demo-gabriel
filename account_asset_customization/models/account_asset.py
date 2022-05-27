# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAsset(models.Model):
    _inherit = 'account.asset'
    # calculate amortization when import, take to much time
    # @api.constrains('name')
    # def _constrains_masive_upload(self):
    #     if self._context.get('import_file', False):
    #         for rec in self:
    #             if rec.journal_id:
    #                 rec.compute_depreciation_board()
