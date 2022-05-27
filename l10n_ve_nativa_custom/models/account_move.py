# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero
import json

class AccountMove(models.Model):
	_inherit = "account.move"

	def _compute_payments_widget_to_reconcile_info(self):
		for move in self:
			move.invoice_outstanding_credits_debits_widget = json.dumps(False)
			move.invoice_has_outstanding = False

			if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
				continue
			pay_term_line_ids = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

			domain = [('account_id', 'in', pay_term_line_ids.mapped('account_id').ids),
					  '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
					  ('partner_id', '=', move.commercial_partner_id.id),
					  ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
					  ('amount_residual_currency', '!=', 0.0)]

			if move.is_inbound():
				domain.extend([('credit', '>', 0), ('debit', '=', 0)])
				type_payment = _('Outstanding credits')
			else:
				domain.extend([('credit', '=', 0), ('debit', '>', 0)])
				type_payment = _('Outstanding debits')
			info = {'title': '', 'outstanding': True, 'content': [], 'move_id': move.id}
			lines = self.env['account.move.line'].search(domain)
			currency_id = move.currency_id
			if len(lines) != 0:
				for line in lines:
					# get the outstanding residual value in invoice currency
					currency = line.company_id.currency_id
					###########################################################################################
					amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
														move.date)
					line.amount_residual_currency = amount_to_show
					##############################################################################################
					if float_is_zero(amount_to_show, precision_rounding=move.currency_id.rounding):
						continue
					info['content'].append({
						'journal_name': line.ref or line.move_id.name,
						'amount': amount_to_show,
						'currency': currency_id.symbol,
						'id': line.id,
						'position': currency_id.position,
						'digits': [69, move.currency_id.decimal_places],
						'payment_date': fields.Date.to_string(line.date),
					})
				info['title'] = type_payment
				move.invoice_outstanding_credits_debits_widget = json.dumps(info)
				move.invoice_has_outstanding = True

	def _get_reconciled_info_JSON_values(self):
		self.ensure_one()

		reconciled_vals = []
		pay_term_line_ids = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
		partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
		for partial in partials:
			counterpart_lines = partial.debit_move_id + partial.credit_move_id
			# In case we are in an onchange, line_ids is a NewId, not an integer. By using line_ids.ids we get the correct integer value.
			counterpart_line = counterpart_lines.filtered(lambda line: line.id not in self.line_ids.ids)

			amount = partial.company_currency_id._convert(partial.amount, self.currency_id, self.company_id, self.date)

			if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
				continue

			ref = counterpart_line.move_id.name
			if counterpart_line.move_id.ref:
				ref += ' (' + counterpart_line.move_id.ref + ')'

			reconciled_vals.append({
				'name': counterpart_line.name,
				'journal_name': counterpart_line.journal_id.name,
				'amount': amount,
				'currency': self.currency_id.symbol,
				'digits': [69, self.currency_id.decimal_places],
				'position': self.currency_id.position,
				'date': counterpart_line.date,
				'payment_id': counterpart_line.id,
				'account_payment_id': counterpart_line.payment_id.id,
				'payment_method_name': counterpart_line.payment_id.payment_method_id.name if counterpart_line.journal_id.type == 'bank' else None,
				'move_id': counterpart_line.move_id.id,
				'ref': ref,
			})
		return reconciled_vals


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	def _reconcile_lines(self, debit_moves, credit_moves, field):
		""" This function loops on the 2 recordsets given as parameter as long as it
			can find a debit and a credit to reconcile together. It returns the recordset of the
			account move lines that were not reconciled during the process.
		"""
		(debit_moves + credit_moves).read([field])
		to_create = []
		cash_basis = debit_moves and debit_moves[0].account_id.internal_type in ('receivable', 'payable') or False
		cash_basis_percentage_before_rec = {}
		dc_vals ={}
		while (debit_moves and credit_moves):
			debit_move = debit_moves[0]
			credit_move = credit_moves[0]
			company_currency = debit_move.company_id.currency_id
			# We need those temporary value otherwise the computation might be wrong below
			temp_amount_residual = min(debit_move.amount_residual, -credit_move.amount_residual)
			temp_amount_residual_currency = min(debit_move.amount_residual_currency, -credit_move.amount_residual_currency)
			dc_vals[(debit_move.id, credit_move.id)] = (debit_move, credit_move, temp_amount_residual_currency)
			amount_reconcile = min(debit_move[field], -credit_move[field])

			#Remove from recordset the one(s) that will be totally reconciled
			# For optimization purpose, the creation of the partial_reconcile are done at the end,
			# therefore during the process of reconciling several move lines, there are actually no recompute performed by the orm
			# and thus the amount_residual are not recomputed, hence we have to do it manually.
			if amount_reconcile == debit_move[field]:
				debit_moves -= debit_move
			else:
				debit_moves[0].amount_residual -= temp_amount_residual
				debit_moves[0].amount_residual_currency -= temp_amount_residual_currency

			if amount_reconcile == -credit_move[field]:
				credit_moves -= credit_move
			else:
				credit_moves[0].amount_residual += temp_amount_residual
				credit_moves[0].amount_residual_currency += temp_amount_residual_currency
			#Check for the currency and amount_currency we can set
			currency = False
			amount_reconcile_currency = 0
			if field == 'amount_residual_currency':
				currency = credit_move.currency_id.id
				amount_reconcile_currency = temp_amount_residual_currency
				amount_reconcile = temp_amount_residual
			elif bool(debit_move.currency_id) != bool(credit_move.currency_id):
				# If only one of debit_move or credit_move has a secondary currency, also record the converted amount
				# in that secondary currency in the partial reconciliation. That allows the exchange difference entry
				# to be created, in case it is needed. It also allows to compute the amount residual in foreign currency.
				currency = debit_move.currency_id or credit_move.currency_id
				currency_date = debit_move.currency_id and credit_move.date or debit_move.date
				###########################################################################################################################################
				amount_reconcile_currency = company_currency._convert(amount_reconcile, currency, debit_move.company_id, credit_move.move_id.date)
				###########################################################################################################################################
				currency = currency.id

			if cash_basis:
				tmp_set = debit_move | credit_move
				cash_basis_percentage_before_rec.update(tmp_set._get_matched_percentage())

			to_create.append({
				'debit_move_id': debit_move.id,
				'credit_move_id': credit_move.id,
				'amount': amount_reconcile,
				'amount_currency': amount_reconcile_currency,
				'currency_id': currency,
			})

		cash_basis_subjected = []
		part_rec = self.env['account.partial.reconcile']
		for partial_rec_dict in to_create:
			debit_move, credit_move, amount_residual_currency = dc_vals[partial_rec_dict['debit_move_id'], partial_rec_dict['credit_move_id']]
			# /!\ NOTE: Exchange rate differences shouldn't create cash basis entries
			# i. e: we don't really receive/give money in a customer/provider fashion
			# Since those are not subjected to cash basis computation we process them first
			if not amount_residual_currency and debit_move.currency_id and credit_move.currency_id:
				part_rec.create(partial_rec_dict)
			else:
				cash_basis_subjected.append(partial_rec_dict)

		for after_rec_dict in cash_basis_subjected:
			new_rec = part_rec.create(after_rec_dict)
			# if the pair belongs to move being reverted, do not create CABA entry
			if cash_basis and not (
					new_rec.debit_move_id.move_id == new_rec.credit_move_id.move_id.reversed_entry_id
					or
					new_rec.credit_move_id.move_id == new_rec.debit_move_id.move_id.reversed_entry_id
			):
				new_rec.create_tax_cash_basis_entry(cash_basis_percentage_before_rec)
		return debit_moves+credit_moves

