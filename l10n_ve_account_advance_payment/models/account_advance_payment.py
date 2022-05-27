# -*- coding: utf-8 -*-

from typing import Counter, Sequence
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from lxml import etree

ADVANCE_PAYMENT_STATES = [
    ('draft', 'Draft'),
    ('cancel', 'Cancel'),
    ('available', 'Available'),
    ('paid', 'Paid'),
]

ADVANCE_APPLY_STATES = [
    ('draft', 'draft'),
    ('cancel', 'Cancel'),
    ('done', 'Done'),
]

READONLY_STATES = dict.fromkeys(['cancel', 'available', 'paid'], [('readonly', True)])
APPLY_READONLY_STATES = dict.fromkeys(['cancel', 'done'], [('readonly', True)])


class AccountAdvancePayment(models.Model):
    _name = 'account.advance.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Account Advance Payment'

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        if self._context.get('default_account_advance_type'):
            res['type'] = self._context['default_account_advance_type']
        return res

    @api.model
    def _get_advance_payment_seq(self, advance):
        sequence_obj = self.env['ir.sequence']
        if advance.type == 'customer':
            return sequence_obj.next_by_code('advance.payment.customer')
        else:
            return sequence_obj.next_by_code('advance.payment.supplier')

    name = fields.Char(default=_('New Advance'), readonly=True, translate=True, copy=False)
    ref = fields.Char('Reference', states=READONLY_STATES, copy=False)
    date_advance = fields.Date(default=lambda self: fields.Date.context_today(self), 
        states=READONLY_STATES, tracking=True)
    partner_id = fields.Many2one('res.partner', states=READONLY_STATES, tracking=True)
    journal_id = fields.Many2one('account.journal', states=READONLY_STATES, tracking=True)
    type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier')
    ], default='customer', states=READONLY_STATES)
    bank_account_id = fields.Many2one('account.journal', domain=[('type', 'in', ['cash', 'bank'])],
        states=READONLY_STATES, tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, 
        states=READONLY_STATES, tracking=True)
    amount_advanced = fields.Monetary(states=READONLY_STATES, tracking=True)
    amount_available = fields.Monetary(readonly=True, copy=False)
    payment_id = fields.Many2one('advance.payment.method', string='Payment Method', 
        states=READONLY_STATES)
    move_id = fields.Many2one('account.move', string='Advance Payment Move', readonly=True, copy=False)
    move_line_ids = fields.One2many('account.move.line', related='move_id.line_ids')
    state = fields.Selection(ADVANCE_PAYMENT_STATES, default=ADVANCE_PAYMENT_STATES[0][0], tracking=True, copy=False)
    advance_apply_ids = fields.One2many('account.advance.payment.apply', 'advance_id', 
        states=READONLY_STATES, copy=False)
    advance_apply_count = fields.Integer(compute='_compute_advance_apply_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
        states=READONLY_STATES)
        
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for advance in self:
            if advance.type == 'customer':
                advance.journal_id = advance.partner_id.journal_advance_sales_id
            else:
                advance.journal_id = advance.partner_id.journal_advance_purchases_id
    
    @api.onchange('bank_account_id')
    def _onchange_bank_account_id(self):
        for advance in self:
            advance.currency_id = advance.bank_account_id.currency_id
    
    # @api.constrains('bank_account_id', 'currency_id')
    # def _check_currency_bank_and_advance(self):
    #     for advance in self:
    #         if advance.bank_account_id.currency_id != advance.currency_id:
    #             raise ValidationError(_('The currency of the bank account must be the same as the' 
    #                 ' currency of the advance payment.'))
    
    @api.constrains('partner_id', 'state')
    def _check_partner_account_fields(self):
        for advance in self:
            if not advance.partner_id:
                continue
            
            if advance.type == 'customer' and not advance.partner_id.journal_advance_sales_id:
                raise ValidationError(_('The journal of down payments for sales is not defined in the' 
                    ' customer.'))
            
            if advance.type == 'customer' and not advance.partner_id.account_advance_sales_id:
                raise ValidationError(_('The accounting account for down payments for sales is not defined' 
                    ' in the customer.'))
            
            if advance.type == 'supplier' and not advance.partner_id.journal_advance_purchases_id:
                raise ValidationError(_('The journal of down payments for purchases is not defined in the' 
                    ' supplier.'))
            
            if advance.type == 'supplier' and not advance.partner_id.account_advance_purchases_id:
                raise ValidationError(_('The accounting account for down payments for purchases is not' 
                    ' defined in the supplier.'))
                
    
    @api.depends('advance_apply_ids', 'advance_apply_ids.state')
    def _compute_advance_apply_count(self):
        for advance in self:
            advance.advance_apply_count = len(advance.advance_apply_ids)
    
    def action_advance_apply_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments from: {}').format(self.name),
            'res_model': 'account.advance.payment.apply',
            'view_mode': 'tree,form',
            'domain': [('advance_id', '=', self.id)],
            'views': self._get_views_form_advance_apply(self.type),
            'context': dict(**self._context, default_advance_id=self.id),
        }
    
    @api.model
    def _get_views_form_advance_apply(self, type_advance):
        if type_advance not in ('customer', 'supplier'):
            return [(False, 'tree'),(False, 'form')]
        
        ir_model = self.env['ir.model.data']
        if type_advance == 'customer':
            tree_xmlid = 'l10n_ve_account_advance_payment.advance_apply_tree'
            form_xmlid = 'l10n_ve_account_advance_payment.advance_apply_form'
            treeview_id = ir_model.xmlid_to_res_id(tree_xmlid, raise_if_not_found=False)
            formview_id = ir_model.xmlid_to_res_id(form_xmlid, raise_if_not_found=False)
            return [(treeview_id, 'tree'), (formview_id, 'form')]
        else:
            tree_xmlid = 'l10n_ve_account_advance_payment.advance_apply_supplier_tree'
            form_xmlid = 'l10n_ve_account_advance_payment.advance_apply_supplier_form'
            treeview_id = ir_model.xmlid_to_res_id(tree_xmlid, raise_if_not_found=False)
            formview_id = ir_model.xmlid_to_res_id(form_xmlid, raise_if_not_found=False)
            return [(treeview_id, 'tree'), (formview_id, 'form')]

    def action_make_available(self):
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'available'
            if self.name in (_('New Advance'), 'New Advance'):
                self.name = self._get_advance_payment_seq(self)
            self.amount_available = self.amount_advanced
        return True

    def action_cancel_advance(self):
        self.ensure_one()
        if self.state == 'available':
            self.state = 'cancel'
            self.amount_available = 0
        return True
    
    def action_return_to_draft(self):
        self.ensure_one()
        if self.state == 'cancel':
            self.state = 'draft'
            self.move_id = False
        return True
    
    def action_apply_to_invoice(self):
        self.ensure_one()
        view_obj = self.env['ir.ui.view'].sudo()
        if self.type == 'customer':
            view_id = view_obj.get_view_id('l10n_ve_account_advance_payment.advance_apply_form')
        else:
            view_id = view_obj.get_view_id('l10n_ve_account_advance_payment.advance_apply_supplier_form')
        action = self.env['account.advance.payment.apply'].get_formview_action()
        action['views'] = [(view_id, 'form')] 
        action['context']['default_advance_id'] = self.id
        if self._context.get('custom_target_apply'):
            action['target'] = self._context['custom_target_apply']
        return action
    
    def apply_amount(self, amount):
        self.ensure_one()
        self.amount_available -= amount
        if self.available_is_zero():
            self.state = 'paid'
        return True
    
    def deapply_amount(self, amount):
        self.ensure_one()
        self.amount_available += amount
        if self.available_is_zero() is False:
            self.state = 'available'
        return True
    
    def available_is_zero(self):
        self.ensure_one()
        currency = self.currency_id
        return float_is_zero(self.amount_available, precision_rounding=currency.rounding)
    
    def action_refund_available(self):
        self.ensure_one()
        return True
    

class AccountAdvancePaymentApply(models.Model):
    _name = 'account.advance.payment.apply'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Advance Payment Apply'

    advance_id = fields.Many2one('account.advance.payment')
    name = fields.Char(compute='_compute_name')
    ref = fields.Char('Reference', states=APPLY_READONLY_STATES, copy=False)
    date_apply = fields.Date(states=APPLY_READONLY_STATES, tracking=True)
    invoice_id = fields.Many2one('account.move', states=APPLY_READONLY_STATES, tracking=True, copy=False)
    invoice_currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    amount_invoice = fields.Monetary(related='invoice_id.amount_residual', 
        currency_field='invoice_currency_id')
    amount_invoice_currency_advance = fields.Monetary(compute='_compute_amount_invoice_currency_advance')
    partner_id = fields.Many2one('res.partner', related='advance_id.partner_id')
    journal_id = fields.Many2one('account.journal', related='advance_id.journal_id')
    amount_advanced = fields.Monetary(related='advance_id.amount_advanced')
    currency_id = fields.Many2one('res.currency', related='advance_id.currency_id')
    # helper field for validations and UI.
    has_different_currency_with_invoice = fields.Boolean(
        compute='_compute_has_different_currency_with_invoice')
    company_id = fields.Many2one('res.company', related='advance_id.company_id')
    amount_available = fields.Monetary(related='advance_id.amount_available')
    amount_apply = fields.Monetary(string='Amount Apply', states=APPLY_READONLY_STATES, tracking=True)
    move_apply_id = fields.Many2one('account.move', string='Apply Payment Move', readonly=True, copy=False)
    move_apply_line_ids = fields.One2many('account.move.line', related='move_apply_id.line_ids')
    state = fields.Selection(ADVANCE_APPLY_STATES, default=ADVANCE_APPLY_STATES[0][0], tracking=True)

    @api.depends('advance_id')
    def _compute_name(self):
        for advance_apply in self:
            advance_apply.name = _('Payment: {}').format(advance_apply.advance_id.name)
    
    @api.depends('invoice_id')
    def _compute_amount_invoice_currency_advance(self):
        for advance_apply in self:
            if advance_apply.invoice_id:
                currency_advance = advance_apply.currency_id
                currency_invoice = advance_apply.invoice_currency_id
                amount = currency_invoice.with_context(date=advance_apply.invoice_id.date).compute(
                    advance_apply.amount_invoice, currency_advance
                )
                advance_apply.amount_invoice_currency_advance = amount
            else:
                advance_apply.amount_invoice_currency_advance = 0
    
    @api.depends('currency_id', 'invoice_currency_id')
    def _compute_has_different_currency_with_invoice(self):
        for advance_apply in self:
            if advance_apply.currency_id != advance_apply.invoice_currency_id:
                advance_apply.has_different_currency_with_invoice = True
            else:
                advance_apply.has_different_currency_with_invoice = False
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        for advance_apply in self:
            amount_apply = min([advance_apply.amount_available, 
                advance_apply.amount_invoice_currency_advance])
            advance_apply.amount_apply = amount_apply
    
    @api.onchange('advance_id')
    def _onchange_advance_id(self):
        today = fields.Date.today()
        for advance_apply in self:
            if advance_apply.advance_id:
                advance_apply.date_apply = advance_apply.advance_id.date_advance
            else:
                advance_apply.date_apply = today
    
    @api.constrains('date_apply')
    def _check_date_apply(self):
        for advance_apply in self:
            if advance_apply.date_apply < advance_apply.advance_id.date_advance:
                raise ValidationError(_('The date of application cannot be less than the date of' 
                    ' registration of the advance.'))
    
    def action_apply_advance(self):
        self.ensure_one()
        if self.state == 'draft':
            self._check_amount_apply()
            self.state = 'done'
            self.advance_id.apply_amount(self.amount_apply)
        return True

    def _check_amount_apply(self):
        self.ensure_one()
                    
        if self.advance_id.available_is_zero():
            raise ValidationError(_('Not available for advance payment'))
        
        if self.amount_apply_is_zero():
            raise ValidationError(_('Must apply an amount greater than 0.'))
        
        if self.amount_apply_compare(self.amount_invoice_currency_advance) == 1:
            raise ValidationError(_('Cannot apply a higher amount to the invoice.'))

        if self.amount_apply_compare(self.amount_available) == 1:
            raise ValidationError(_('Cannot apply more than the amount available.'))

        return True
    
    def amount_apply_is_zero(self):
        self.ensure_one()
        currency = self.currency_id
        return float_is_zero(self.amount_apply, precision_rounding=currency.rounding)
    
    def amount_apply_compare(self, other_amount):
        self.ensure_one()
        currency = self.currency_id
        return float_compare(self.amount_apply, other_amount, precision_rounding=currency.rounding)

    def action_cancel_advance_apply(self):
        self.ensure_one()
        if self.state == 'done':
            self.state = 'cancel'
            self.advance_id.deapply_amount(self.amount_apply)
        return True

    def action_return_to_draft(self):
        self.ensure_one()
        if self.state == 'cancel':
            self.state = 'draft'
            self.move_apply_id = False
        return True
    
    def get_report_payment_action(self):
        report_name = 'l10n_ve_account_advance_payment.report_advance_payment_receipt'
        payment_report = self.env['ir.actions.report']._get_report_from_name(report_name)
        return payment_report.report_action(self.ids)
