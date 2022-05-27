from odoo import api, fields, models, _
from odoo.exceptions import UserError

#Fecha en la cual se empieza a aplicar la reforma del IGTF.
IGTF_APPLY_DATE = '2022-03-28'


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_tranfer', 'Bank Transfer')
    ], default='cash',
        readonly=True,
        states={'draft': [('readonly',False)]},
        string='Método de pago IGTF'
    )
    payment_foreign_currency = fields.Boolean(
        compute='_compute_payment_foreign_currency',
    )
    apply_igtf = fields.Boolean(
        compute='_compute_apply_igtf',
        store=True,
        copy=False
    )
    igtf_account_id = fields.Many2one('account.account',
        domain="[('internal_type', '=', 'liquidity')]",
        readonly=True,
        states={'draft': [('readonly',False)]}
    )
    igtf_move_id = fields.Many2one('account.move', copy=False)

    @api.depends(
        'company_id',
        'payment_method',
        'currency_id',
        'journal_id',
        'journal_id.currency_id'
    )
    def _compute_payment_foreign_currency(self):
        for payment in self:
            company = payment.company_id or self.env.company
            igtf_exempt_currency_ids = company.igtf_exempt_currency_ids
            currency = payment.currency_id
            journal_currency  = payment.journal_id.currency_id
            payment.payment_foreign_currency = (
                currency not in igtf_exempt_currency_ids and
                journal_currency not in igtf_exempt_currency_ids
            )

    @api.depends(
        'company_id',
        'payment_method',
        'payment_date',
        'payment_type',
        'partner_id',
        'currency_id',
        'journal_id',
        'journal_id.currency_id'
    )
    def _compute_apply_igtf(self):
        for payment in self:
            payment.apply_igtf = payment._check_apply_igtf() 

    def _prepare_igtf_move_values(self):
        self.ensure_one()
        
        company = self.company_id or self.env.company
        igtf_perc = company.igtf_percentaje / 100.0
        currency = self.currency_id
        igtf_amount = currency.round(self.amount * igtf_perc)
        igtf_amount_company_curr = currency._convert(igtf_amount,
            company.currency_id, company, self.payment_date
        )
        account_bank = self.igtf_account_id

        if self.payment_type == 'inbound':
            journal = company.igtf_sale_journal_id
            account_igtf = company.igtf_sale_account_id
            if not journal:
                raise UserError('Debe definir el diario para IGTF'
                    ' en la configuracion del la compañia.'
                )
            if not account_igtf:
                raise UserError('Debe definir la cuenta contable para IGTF'
                    ' en la configuracion de la compañia'
                )
            debit_vals = {
                'name': 'Pago retencion IGTF',
                'currency_id': currency.id,
                'account_id': account_bank.id,
                'debit': igtf_amount_company_curr,
                'credit': 0.0,
                'amount_currency': igtf_amount,
                'partner_id': self.partner_id.id,
            }
            credit_vals = {
                'name': 'Retencion IGTF',
                'currency_id': currency.id,
                'account_id': account_igtf.id,
                'debit': 0.0,
                'credit': igtf_amount_company_curr,
                'amount_currency': -igtf_amount,
                'partner_id': company.partner_id.id
            }
        else:
            journal = company.igtf_purchase_journal_id
            account_igtf = company.igtf_purchase_account_id
            if not journal:
                raise UserError('Debe definir el diario para IGTF'
                    ' en la configuracion del la compañia.'
                )
            if not account_igtf:
                raise UserError('Debe definir la cuenta contable para IGTF'
                    ' en la configuracion de la compañia'
                )
            debit_vals = {
                'name': 'Retencion IGTF',
                'currency_id': currency.id,
                'account_id': account_igtf.id,
                'debit': igtf_amount_company_curr,
                'credit': 0.0,
                'amount_currency': igtf_amount,
                'partner_id': company.partner_id.id,
            }
            credit_vals = {
                'name': 'Pago retencion IGTF',
                'currency_id': currency.id,
                'account_id': account_bank.id,
                'debit': 0.0,
                'credit': igtf_amount_company_curr,
                'amount_currency': -igtf_amount,
                'partner_id': self.partner_id.id,
            }

        move_vals = {
            'ref': 'Retencion IGTF: %s' %self.name,
            'date': self.payment_date,
            'journal_id': journal.id,
            'company_id': company.id,
            'currency_id': currency.id,
            'partner_id': self.partner_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'type': 'entry'
        }
        return move_vals

    def create_igtf_move(self):
        self.ensure_one()
        move_values = self._prepare_igtf_move_values()
        move = self.env['account.move'].create(move_values)
        move.post()
        self.igtf_move_id = move
        return move

    def update_igtf_move(self):
        self.ensure_one()
        move_values = self._prepare_igtf_move_values()
        update_values = {
            'partner_id': move_values['partner_id'],
            'company_id': move_values['company_id'],
            'currency_id': move_values['currency_id'],
            'ref': move_values['ref'],
            'date': move_values['date'],
            'line_ids': move_values['line_ids']
        }
        self.igtf_move_id.line_ids.unlink()
        self.igtf_move_id.write(update_values)
        self.igtf_move_id.post()
        return self.igtf_move_id

    def _check_apply_igtf(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        payment_method_cash = self.payment_method == 'cash'
        foreign_currency = self.payment_foreign_currency
        partner = self.partner_id
        payment_in_igtf_apply_date = (
            self.payment_date.strftime('%Y-%m-%d') >= IGTF_APPLY_DATE
        )
        if self.payment_type == 'inbound':
            return (
                payment_method_cash and
                company.is_special_taxpayer_igtf and 
                foreign_currency and
                payment_in_igtf_apply_date
            )
        elif self.payment_type == 'outbound':
            return (
                partner.is_special_taxpayer_igtf and
                foreign_currency and
                payment_in_igtf_apply_date
            )

        return False

    def post(self):
        res = super().post()
        payments_with_igtf = self.filtered(
            lambda r: r.apply_igtf
        )
        for payment in payments_with_igtf:
            if not payment.igtf_move_id:
                payment.create_igtf_move()
            else:
                if payment.igtf_move_id.state == 'draft':
                    payment.update_igtf_move()
        return res

    def action_draft(self):
        super().action_draft()
        igtf_moves = self.filtered(
            lambda r: r.apply_igtf and r.igtf_move_id
        ).mapped('igtf_move_id')
        igtf_moves.filtered(lambda r: r.state != 'draft').button_draft()

    def cancel(self):
        super().cancel()
        igtf_moves = self.filtered(
            lambda r: r.apply_igtf and r.igtf_move_id
        ).mapped('igtf_move_id')
        posted_moves = igtf_moves.filtered(
            lambda r: r.state == 'posted'
        )
        posted_moves.button_draft()
        posted_moves.button_cancel()
        igtf_moves.filtered(
            lambda r: r.state == 'draft'
        ).button_cancel()
