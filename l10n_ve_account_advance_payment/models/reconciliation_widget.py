from odoo import api, models
from odoo.osv import expression

class AccountReconciliation(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'
	
	@api.model
	def _domain_move_lines_for_reconciliation(self, st_line, aml_accounts, partner_id, excluded_ids=[], search_str=False, mode='rp'):
		""" Return the domain for account.move.line records which can be used for bank statement reconciliation.

			:param aml_accounts:
			:param partner_id:
			:param excluded_ids:
			:param search_str:
			:param mode: 'rp' for receivable/payable or 'other'
		"""
		AccountMoveLine = self.env['account.move.line']

		#Always exclude the journal items that have been marked as 'to be checked' in a former bank statement reconciliation
		to_check_excluded = AccountMoveLine.search(AccountMoveLine._get_suspense_moves_domain()).ids
		excluded_ids.extend(to_check_excluded)

		domain_reconciliation = [
			'&', '&', '&',
			('statement_line_id', '=', False),
			('account_id', 'in', aml_accounts),
			('balance', '!=', 0.0),
			'|',
			('payment_id', '<>', False),
			('payment_advance_id', '<>', False),
		]

		# default domain matching
		domain_matching = [
			'&', '&',
			('reconciled', '=', False),
			('account_id.reconcile', '=', True),
			('balance', '!=', 0.0),
		]

		domain = expression.OR([domain_reconciliation, domain_matching])
		if partner_id:
			domain = expression.AND([domain, [('partner_id', '=', partner_id)]])
		if mode == 'rp':
			domain = expression.AND([domain,
			[('account_id.internal_type', 'in', ['receivable', 'payable', 'liquidity'])]
			])
		else:
			domain = expression.AND([domain,
			[('account_id.internal_type', 'not in', ['receivable', 'payable', 'liquidity'])]
			])

		# Domain factorized for all reconciliation use cases
		if search_str:
			str_domain = self._domain_move_lines(search_str=search_str)
			str_domain = expression.OR([
				str_domain,
				[('partner_id.name', 'ilike', search_str)]
			])
			domain = expression.AND([
				domain,
				str_domain
			])

		if excluded_ids:
			domain = expression.AND([
				[('id', 'not in', excluded_ids)],
				domain
			])
		# filter on account.move.line having the same company as the statement line
		domain = expression.AND([domain, [('company_id', '=', st_line.company_id.id)]])

		# take only moves in valid state. Draft is accepted only when "Post At" is set
		# to "Bank Reconciliation" in the associated journal
		domain_post_at = [
			'|', '&',
			('move_id.state', '=', 'draft'),
			('journal_id.post_at', '=', 'bank_rec'),
			('move_id.state', 'not in', ['draft', 'cancel']),
		]
		domain = expression.AND([domain, domain_post_at])

		if st_line.company_id.account_bank_reconciliation_start:
			domain = expression.AND([domain, [('date', '>=', st_line.company_id.account_bank_reconciliation_start)]])
		return domain