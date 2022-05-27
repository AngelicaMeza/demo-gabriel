# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountAdvancePayment(models.Model):
    _inherit = 'account.advance.payment'

    igtf_move_id = fields.Many2one('account.move')
    # payment_advance_id_igtf_check = fields.Boolean('Check', compute='_compute_payment_advance_id', store=True)

    # @api.depends('igtf_move_id.line_ids')
    # def _compute_payment_advance_id(self):
    #     for payment in self:
    #         if not payment.payment_advance_id_igtf_check:
    #             for line in payment.igtf_move_id.line_ids:
    #                 if not line.payment_advance_id:
    #                     line.update({'payment_advance_id': payment.id})
    #             payment.payment_advance_id_igtf_check = True

    def _check_journal_withholding_igtf(self):
        self.ensure_one()
        return self.bank_account_id.calculate_wh_itf
    
    def _get_igtf_percertaje(self):
        self.ensure_one()
        return self.bank_account_id.wh_porcentage
    
    def _check_advance_type(self):
        self.ensure_one()
        return True if self.type == 'supplier' else False
    
    def _check_partner_vat(self):
        self.ensure_one()
        vat_distinct = True
        partner = self.partner_id

        if partner.type == 'company':
            if partner.vat == self.company_id.partner_id.vat:
                vat_distinct = False
        elif partner.type == 'person':
            if partner.identification_id == self.company_id.partner_id.vat:
                vat_distinct = False
        
        return vat_distinct
    
    def _apply_igtf_withholding(self):
        self.ensure_one()
        apply_journal_igtf = self._check_journal_withholding_igtf()
        apply_advance_type = self._check_advance_type()
        partner_valid_vat = self._check_partner_vat()

        if apply_advance_type and apply_journal_igtf and partner_valid_vat:
            return True
        else:
            return False
    
    def _get_igtf_sequence(self):
        self.ensure_one()
        SEQUENCE_CODE = 'l10n_account_withholding_itf'
        company_id = self.env.company
        IrSequence = self.env['ir.sequence'].with_context(
            force_company=company_id.id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # if a sequence does not yet exist for this company create one
        if not name:
            IrSequence.sudo().create({
                'prefix': 'IGTF',
                'name': 'Localización Venezolana impuesto IGTF %s' % company_id.id,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': company_id.id,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def create_igtf_move(self):
        self.ensure_one()

        name = self._get_igtf_sequence()
        vals = {
            'name': name,
            'date': self.date_advance,
            'journal_id': self.bank_account_id.id,
            'line_ids': False,
            'state': 'draft',
            'type': 'entry',
            'advance_id': self.id,
        }

        move_obj = self.env['account.move']
        move_id = move_obj.create(vals)
        percentage_igtf = self._get_igtf_percertaje()

        if self.currency_id == self.company_id.currency_id:
            currency = False
            amount_currency = 0
            amount_igtf = round(self.amount_advanced * (percentage_igtf / 100), 2)
        else:
            currency = self.currency_id.id
            amount_currency = self.amount_advanced
            amount_igtf = self.currency_id._convert(self.amount_advanced, self.company_id.currency_id,
                self.company_id, self.date_advance)
            amount_igtf = round(amount_igtf * (percentage_igtf / 100), 2)

        move = {
            'account_id': self.bank_account_id.default_credit_account_id.id,
            'company_id': self.company_id.id,
            'currency_id': currency,
            'date_maturity': False,
            'ref': "Comisión del %s %% del pago %s por comisión" % (percentage_igtf, self.name),
            'date': self.date_advance,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'name': "Comisión del %s %% del pago %s por comisión" % (percentage_igtf, self.name),
            'journal_id': self.journal_id.id,
            'credit': amount_igtf,
            'debit': 0.0,
            'amount_currency': -amount_currency,
            'payment_advance_id': self.id,
        }

        move_line_obj = self.env['account.move.line']
        move_line_id1 = move_line_obj.with_context(
            check_move_validity=False).create(move)
        move['amount_currency'] = amount_currency
        move['account_id'] = self.bank_account_id.account_wh_itf_id.id
        move['credit'] = 0.0
        move['debit'] = amount_igtf

        move_line_id2 = move_line_obj.create(move)

        if move_line_id1 and move_line_id2:
            move_id.action_post()
        return move_id

    def action_make_available(self):
        res = super().action_make_available()

        if self._apply_igtf_withholding():
            self.igtf_move_id = self.create_igtf_move()

        return res

    def action_cancel_advance(self):
        res = super().action_cancel_advance()
        if self.igtf_move_id:
            default_values = {
                'advance_id': self.id,
                'ref': 'Reversión de: {}'.format(self.igtf_move_id.name)
            }
            self.igtf_move_id._reverse_moves(default_values_list=[default_values], cancel=True)
        return res        