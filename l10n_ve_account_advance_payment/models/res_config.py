# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_journal_advance_sales_id = fields.Many2one('account.journal', default_model='res.partner')
    default_journal_advance_purchases_id = fields.Many2one('account.journal', default_model='res.partner')
    default_account_advance_sales_id = fields.Many2one('account.account', default_model='res.partner', 
        domain=[('deprecated', '=', False)])
    default_account_advance_purchases_id = fields.Many2one('account.account', default_model='res.partner',
        domain=[('deprecated', '=', False)])