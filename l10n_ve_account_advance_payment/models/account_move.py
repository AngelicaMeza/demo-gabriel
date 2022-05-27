# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    advance_id = fields.Many2one('account.advance.payment', copy=False)
    # invoice fields
    advance_payment_ids = fields.One2many('account.advance.payment.apply', 'invoice_id', string='Advance Payments')
    amount_advance_available_customer = fields.Monetary(related='partner_id.customer_advance_available',
        currency_field='company_currency_id')
    amount_advance_available_invoice_customer  = fields.Monetary(compute='_compute_amount_advance_available_invoice_customer')
    amount_advance_available_supplier = fields.Monetary(related='partner_id.supplier_advance_available',
        currency_field='company_currency_id')
    amount_advance_available_invoice_supplier  = fields.Monetary(compute='_compute_amount_advance_available_invoice_supplier')
    invoice_in_foreign_currency = fields.Boolean(compute='_compute_invoice_in_foreign_currency')
    # helper ui fields
    apply_advance_btn_visible = fields.Boolean(compute='_compute_apply_advance_btn_visible')

    @api.depends('partner_id', 'type', 'state', 'invoice_payment_state', 'amount_advance_available_customer', 'amount_advance_available_supplier')
    def _compute_apply_advance_btn_visible(self):
        for move in self:
            # button invisible for not invoices
            no_invoices = self.filtered(lambda m: not m.is_invoice(include_receipts=True))
            no_invoices.apply_advance_btn_visible = False
            invoices = self - no_invoices
            for inv in invoices:
                currency = inv.company_currency_id
                visible_state = inv.state in ('draft', 'posted')
                payment_visible_state = inv.invoice_payment_state not in ('in_payment', 'paid')
                amount_available = not float_is_zero(inv.get_invoice_type_advance_available(), 
                    precision_rounding=currency.rounding)
                partner_id = inv.partner_id
                # button invisible for any false value
                inv.apply_advance_btn_visible = (partner_id and amount_available and 
                    visible_state  and payment_visible_state)

    def get_invoice_type_advance_available(self):
        self.ensure_one()
        if self.is_sale_document(include_receipts=True):
            return self.amount_advance_available_customer
        else:
            return self.amount_advance_available_supplier


    @api.depends('currency_id', 'company_currency_id')
    def _compute_invoice_in_foreign_currency(self):
        for invoice in self:
            if invoice.currency_id != invoice.company_currency_id:
                invoice.invoice_in_foreign_currency = True
            else:
                invoice.invoice_in_foreign_currency = False

    @api.depends('amount_advance_available_customer', 'currency_id', 'company_currency_id')
    def _compute_amount_advance_available_invoice_customer(self):
        today = fields.Date.today()   
        for invoice in self:
            company_currency = invoice.company_currency_id.with_context(date=today)
            amount = company_currency.compute(invoice.amount_advance_available_customer, invoice.currency_id)
            invoice.amount_advance_available_invoice_customer = amount
    
    @api.depends('amount_advance_available_supplier', 'currency_id', 'company_currency_id')
    def _compute_amount_advance_available_invoice_supplier(self):
        today = fields.Date.today()   
        for invoice in self:
            company_currency = invoice.company_currency_id.with_context(date=today)
            amount = company_currency.compute(invoice.amount_advance_available_supplier, invoice.currency_id)
            invoice.amount_advance_available_invoice_supplier = amount
    
    def get_contact_type(self):
        self.ensure_one()
        if self.is_sale_document(include_receipts=True):
            return 'cliente'
        if self.is_purchase_document(include_receipts=True):
            return 'proveedor'
        return 'contacto'

    def action_get_advance_available(self):
        self.ensure_one()
        advance_obj = self.env['account.advance.payment']
        partner = self.partner_id
        if not partner:
            contact_type = self.get_contact_type()
            raise UserError('La factura debe tener indicado un %s' %contact_type)
        
        domain = [('partner_id', '=', partner.id), ('state', '=', 'available')]
        advances = advance_obj.search(domain)
        if not advances:
            raise UserError('No hay anticipo disponible.')
        tree_view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'l10n_ve_account_advance_payment.advance_payment_from_invoice_view_tree', 
            raise_if_not_found=False
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aplicar Anticipos Disponibles',
            'res_model': 'account.advance.payment',
            'domain': [('id', 'in', advances.ids)],
            'view_mode': 'tree',
            'views': [(tree_view_id, 'tree')],
            'target': 'new',
            'context': {'create': False, 'delete': False, 'edit': False, 'duplicate': False, 'default_invoice_id': self.id}
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    advance_id = fields.Many2one('account.advance.payment', related='move_id.advance_id')
    payment_advance_id = fields.Many2one('account.advance.payment', string="Originator Payment", copy=False, help="Payment that created this entry")