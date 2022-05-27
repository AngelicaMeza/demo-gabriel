# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    journal_advance_sales_id = fields.Many2one('account.journal')
    journal_advance_purchases_id = fields.Many2one('account.journal')
    account_advance_sales_id = fields.Many2one('account.account', 
        domain=[('deprecated', '=', False)])
    account_advance_purchases_id = fields.Many2one('account.account', 
        domain=[('deprecated', '=', False)])
    customer_advance_available = fields.Monetary(compute='_compute_customer_advance_available')
    supplier_advance_available = fields.Monetary(compute='_compute_supplier_advance_available')

    def _compute_customer_advance_available(self):
        domain = [
            ('advance_id', '!=', False),
            ('advance_id.type', '=', 'customer'), 
            ('partner_id', 'in', self.ids),
            ('account_id.internal_type', '=', 'payable'),
        ]
        default_values = (0, 0)
        fields = ['partner_id', 'debit:sum', 'credit:sum']
        groupby = ['partner_id']
        group_data = self.env['account.move.line'].read_group(domain,fields, groupby)
        partners_data = {p['partner_id'][0]: (p['debit'], p['credit']) for p in group_data}
        for partner in self:
            debit, credit = partners_data.get(partner.id, default_values)
            partner.customer_advance_available = credit - debit
    
    def _compute_supplier_advance_available(self):
        domain = [
            ('advance_id', '!=', False),
            ('advance_id.type', '=', 'supplier'), 
            ('partner_id', 'in', self.ids),
            ('account_id.internal_type', '=', 'receivable'),
        ]
        default_values = (0, 0)
        fields = ['partner_id', 'debit:sum', 'credit:sum']
        groupby = ['partner_id']
        group_data = self.env['account.move.line'].read_group(domain,fields, groupby)
        partners_data = {p['partner_id'][0]: (p['debit'], p['credit']) for p in group_data}
        for partner in self:
            debit, credit = partners_data.get(partner.id, default_values)
            partner.supplier_advance_available = debit - credit
    
    def open_move_lines_advance_customer(self):
        self.ensure_one()
        domain = [
            ('advance_id', '!=', False),
            ('advance_id.type', '=', 'customer'), 
            ('partner_id', '=', self.id),
            ('account_id.internal_type', '=', 'payable'), 
        ]
        views = [self._get_move_line_treeview()]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Advances move of {}').format(self.name),
            'res_model': 'account.move.line',
            'view_mode': 'tree',
            'views': views,
            'domain': domain,
            'context': dict(self._context, search_default_group_by_partner=True, delete=False)
        }

    def open_move_lines_advance_supplier(self):
        self.ensure_one()
        domain = [
            ('advance_id', '!=', False),
            ('advance_id.type', '=', 'supplier'), 
            ('partner_id', '=', self.id),
            ('account_id.internal_type', '=', 'receivable'), 
        ]
        views = [self._get_move_line_treeview()]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Advances move of {}').format(self.name),
            'res_model': 'account.move.line',
            'view_mode': 'tree',
            'views': views,
            'domain': domain,
            'context': dict(self._context, search_default_group_by_partner=True, delete=False)
        }
    
    @api.model
    def _get_move_line_treeview(self):
        ir_model = self.env['ir.model.data']
        xml_id = 'l10n_ve_account_advance_payment.advance_journal_entry_tree'
        treeview_id = ir_model.xmlid_to_res_id(xml_id, raise_if_not_found=False)
        return (treeview_id, 'tree')
