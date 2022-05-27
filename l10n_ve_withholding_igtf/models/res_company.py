from odoo import api, fields, models


class ResCompany(models.Model):
	_inherit = 'res.company'

	igtf_exempt_currency_ids = fields.Many2many('res.currency', 
		help='Currencies of national issuance, IGTF exempted.'
	)
	igtf_sale_account_id = fields.Many2one('account.account',
		help='Accounting account for IGTF withholdings for sales.'
	)
	igtf_sale_journal_id = fields.Many2one('account.journal',
		help='Accounting journal for IGTF withholdings for sales.'
	)
	igtf_purchase_account_id = fields.Many2one('account.account',
		help='Accounting account for IGTF withholdings for purchases.'
	)
	igtf_purchase_journal_id = fields.Many2one('account.journal',
		help='Accounting journal for IGTF withholdings for purchases.'
	)
	is_special_taxpayer_igtf = fields.Boolean(
		help='Indicates that the company is a special taxpayer for' 
		' IGTF withholding.'
	)
	igtf_percentaje = fields.Float(string='IGTF Rate (%)')
