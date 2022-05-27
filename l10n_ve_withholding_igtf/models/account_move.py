from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    possible_payment_currency_id = fields.Many2one('res.currency',
        readonly=True,
        states={'draft': [('readonly',False)]}
    )
    possible_payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_tranfer', 'Bank Transfer'),
    ], 
        readonly=True,
        states={'draft': [('readonly',False)]} 
    )
    payment_foreign_currency = fields.Boolean(
        compute='_compute_payment_foreign_currency'
    )
    igtf_invoice_amount = fields.Monetary(
        compute='_compute_igtf_invoice_amount',
        store=True,
        copy=False
    )
    igtf_invoice_amount_company_currency = fields.Monetary(
        compute='_compute_igtf_invoice_amount',
        store=True,
        copy=False,
        currency_field='company_currency_id'
    )
    igtf_move_ids = fields.Many2many('account.move',
        compute='_compute_igtf_move_ids'
    )

    @api.depends(
        'possible_payment_currency_id',
        'company_id',
    )
    def _compute_payment_foreign_currency(self):
        for move in self:
            company = move.company_id
            igtf_exempt_currency_ids = (
                company.igtf_exempt_currency_ids
            )
            possible_payment_currency_id = (
                move.possible_payment_currency_id
            )

            if (not company or not igtf_exempt_currency_ids
                or not possible_payment_currency_id):
                move.payment_foreign_currency = False
                continue

            move.payment_foreign_currency = (
                possible_payment_currency_id not in 
                igtf_exempt_currency_ids
            )

    @api.depends(
        'payment_foreign_currency',
        'possible_payment_method',
        'amount_total',
        'amount_total_signed'
    )
    def _compute_igtf_invoice_amount(self):
        for move in self:
            payment_method = move.possible_payment_method
            igtf_perc = move.company_id.igtf_percentaje

            if not move.payment_foreign_currency or not payment_method:
                move.igtf_invoice_amount = 0.0
                move.igtf_invoice_amount_company_currency = 0.0
                continue

            move.igtf_invoice_amount = (
                move.amount_total * (igtf_perc/100.0)
            )
            move.igtf_invoice_amount_company_currency = (
                abs(move.amount_total_signed) * (igtf_perc/100.0)
            )

    @api.depends(
        'line_ids',
        'line_ids.matched_debit_ids',
        'line_ids.matched_debit_ids.debit_move_id',
        'line_ids.matched_credit_ids',
        'line_ids.matched_credit_ids.credit_move_id',
    )
    def _compute_igtf_move_ids(self):
        for move in self:
            payments = move._get_reconciled_payments()
            move.igtf_move_ids = payments.mapped('igtf_move_id')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    igtf_line_payment = fields.Boolean()