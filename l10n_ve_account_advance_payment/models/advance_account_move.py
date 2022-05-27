# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAdvanceRegister(models.Model):
    _inherit = 'account.advance.payment'

    # payment_advance_id_check = fields.Boolean('Check', compute='_compute_payment_advance_id', store=True)

    # @api.depends('move_line_ids.payment_advance_id')
    # def _compute_payment_advance_id(self):
    #     for rec in self:
    #         if not rec.payment_advance_id_check:
    #             for line in rec.move_line_ids:
    #                 if not line.payment_advance_id:
    #                     line.update({'payment_advance_id': rec.id})
    #             rec.payment_advance_id_check = True

    def journal_entries_view(self):
        self.ensure_one()
        tree_view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'l10n_ve_account_advance_payment.advance_journal_entry_tree', 
            raise_if_not_found=False
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries: {}').format(self.name),
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (False, 'form')],
            'domain': [('advance_id', '=', self.id)],
            'context':  dict(**self._context, edit=False)
        }
    
    def action_make_available(self):
        res = super().action_make_available()
        self._account_register_advance() 
        return res
    
    def _account_register_advance(self):
        self.ensure_one()
        move_vals = self._prepare_move_vals()
        move = self.env['account.move'].create(move_vals)
        
        move_line_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        debit_vals, credit_vals = self._prepare_move_line_vals()
        debit_vals['move_id'] = move.id
        credit_vals['move_id'] = move.id

        move_line_obj.create(debit_vals)
        move_line_obj.create(credit_vals)
        move.action_post()
        self.move_id = move
        return move
    
    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            'date': self.date_advance,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'line_ids': False,
            'state': 'draft',
            'type': 'entry',
            'advance_id': self.id,
        }
    
    def _get_debit_account_id(self):
        if self.type == 'customer':
            return self.bank_account_id.default_debit_account_id.id
        else:
            return self.partner_id.account_advance_purchases_id.id
    
    def _get_reversal_debit_account_id(self):
        if self.type == 'customer':
            return self.partner_id.account_advance_sales_id.id
        else:
            return self.bank_account_id.default_credit_account_id.id
    
    def _get_credit_account_id(self):
        if self.type == 'customer':
            return self.partner_id.account_advance_sales_id.id
        else:
            return self.bank_account_id.default_credit_account_id.id
    
    def _get_reversal_credit_account_id(self):
        if self.type == 'customer':
            return self.bank_account_id.default_debit_account_id.id
        else:
            return self.partner_id.account_advance_purchases_id.id
    
    def _get_default_move_line_vals(self):
        return {
            'company_id': self.company_id.id,
            'date_maturity': False,
            'name': self.ref,
            'date': self.date_advance,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'payment_advance_id': self.id,
        }
    
    def _prepare_move_line_vals(self):
        self.ensure_one()

        debit_account_id = self._get_debit_account_id()
        credit_account_id = self._get_credit_account_id()
        debit_vals = self._get_default_move_line_vals()
        credit_vals = self._get_default_move_line_vals()

        currency_advance = self.currency_id
        currency_company = self.company_id.currency_id
        if currency_advance != currency_company:
            amount = currency_advance.with_context(date=self.date_advance).compute(
                self.amount_advanced, currency_company)
            amount_currency = self.amount_advanced
            debit_vals['currency_id'] = currency_advance.id
            credit_vals['currency_id'] = currency_advance.id
        else:
            amount  = self.amount_advanced
            amount_currency = 0

        debit_vals.update({
            'account_id': debit_account_id,
            'debit': amount,
            'credit': 0,
            'amount_currency': amount_currency,
        })
        
        credit_vals.update({
            'account_id': credit_account_id,
            'credit': amount,
            'debit': 0,
            'amount_currency': -amount_currency,
        })

        return debit_vals, credit_vals

    def action_cancel_advance(self):
        res = super().action_cancel_advance()
        if self.has_applied_lines():
            raise UserError(_(
                'The advance payment has been applied to invoices, it cannot be cancelled.'))
        self._account_cancel_advance()
        return res
    
    def _account_cancel_advance(self):
        self.ensure_one()
        default_values = {
            'advance_id': self.id,
            'ref': _('Reversal of: {}').format(self.move_id.name)
        }
        move = self.move_id._reverse_moves(default_values_list=[default_values], cancel=True)
        return move
    
    def has_applied_lines(self):
        self.ensure_one()
        return len(self.advance_apply_ids.filtered(lambda l: l.state == 'done')) > 0
    
    def unlink(self):
        advance_not_draft = self.filtered(lambda r: r.state != 'draft')
        if advance_not_draft:
            raise UserError(_('You cannot delete payment advances that are not in draft.'))

        domain = [('type', '=', 'entry'), ('advance_id', 'in', self.ids)]
        move_count = self.env['account.move'].search_count(domain)
        if move_count > 0:
            raise UserError(_('You cannot eliminate payment advances that have already created' 
                ' accounting entries.'))

        return super().unlink()


class AccountAdvanceApply(models.Model):
    _inherit = 'account.advance.payment.apply'

    def action_apply_advance(self):
        res = super().action_apply_advance()
        self._account_apply_advance()
        self._reconcile_payment()
        return res
    
    def _account_apply_advance(self):
        self.ensure_one()
        move_vals = self._prepare_move_vals()
        move = self.env['account.move'].create(move_vals)

        move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit_vals, credit_vals = self._prepare_move_line_vals()
        debit_vals['move_id'] = move.id    
        credit_vals['move_id'] = move.id
        move_line_obj.create(debit_vals)
        move_line_obj.create(credit_vals)
        move.action_post()
        self.move_apply_id = move
        return move
    
    def _reconcile_payment(self):
        self.ensure_one()
        if self.advance_id.type == 'customer':
            destination_account_id = self._get_credit_account_id()  
        else: 
            destination_account_id = self._get_debit_account_id()
        move_lines = self.invoice_id.line_ids + self.move_apply_line_ids
        lines_to_reconcile = move_lines.filtered(lambda r: 
            r.account_id.id == destination_account_id)
        return lines_to_reconcile.reconcile()
  
    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            'date': self.date_apply,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'line_ids': False,
            'state': 'draft',
            'type': 'entry',
            'advance_id': self.advance_id.id,
        }
    
    def _get_debit_account_id(self):
        if self.advance_id.type == 'customer':
            return self.partner_id.account_advance_sales_id.id
        else:
            return self.partner_id.property_account_payable_id.id

    def _get_reversal_debit_account_id(self):
        if self.advance_id.type == 'customer':
            return self.partner_id.property_account_receivable_id.id
        else:
            return self.partner_id.account_advance_purchases_id.id
    
    def _get_credit_account_id(self):
        if self.advance_id.type == 'customer':
            return self.partner_id.property_account_receivable_id.id
        else:
            return self.partner_id.account_advance_purchases_id.id
    
    def _get_reversal_credit_account_id(self):
        if self.advance_id.type == 'customer':
            return self.partner_id.account_advance_sales_id.id
        else:
            return self.partner_id.property_account_payable_id.id
    
    def _get_default_move_line_vals(self):
        return {
            'company_id': self.company_id.id,
            'date_maturity': False,
            'name': self.ref,
            'date': self.date_apply,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
        }
    
    def _prepare_move_line_vals(self):
        self.ensure_one()

        debit_account_id = self._get_debit_account_id()
        credit_account_id = self._get_credit_account_id()
        debit_vals = self._get_default_move_line_vals()
        credit_vals = self._get_default_move_line_vals()

        currency_advance = self.currency_id
        currency_company = self.company_id.currency_id
        if currency_advance != currency_company:
            amount = currency_advance.with_context(date=self.advance_id.date_advance).compute(
                self.amount_apply, currency_company)
            amount_currency = self.amount_apply
            debit_vals['currency_id'] = currency_advance.id
            credit_vals['currency_id'] = currency_advance.id
        else:
            amount = self.amount_apply
            amount_currency = 0

        
        debit_vals.update({
            'account_id': debit_account_id,
            'debit': amount,
            'credit': 0,
            'amount_currency': amount_currency,
        })

       
        credit_vals.update({
            'account_id': credit_account_id,
            'credit': amount,
            'debit': 0,
            'amount_currency': -amount_currency,
        })

        return debit_vals, credit_vals

    def action_cancel_advance_apply(self):
        res = super().action_cancel_advance_apply()
        self._account_cancel_advance_apply()
        return res

    def _account_cancel_advance_apply(self):
        self.ensure_one()
        default_values = {
            'advance_id': self.advance_id.id,
            'ref': _('Reversal of: {}').format(self.move_apply_id.name),
        }
        move = self.move_apply_id._reverse_moves(default_values_list=[default_values], cancel=True)
        return move
    
    def unlink(self):
        payment_not_draft = self.filtered(lambda r: r.state != 'draft')
        if payment_not_draft:
            raise UserError(_('You cannot delete payments that are not in draft.'))

        domain = [('type', '=', 'entry'), ('advance_id', 'in', self.mapped('advance_id').ids)]
        move_count = self.env['account.move'].search_count(domain)
        if move_count > 0:
            raise UserError(_('You cannot eliminate payments that have already created' 
                ' accounting entries.'))

        return super().unlink()
