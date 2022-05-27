# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountMove(models.Model):
	_inherit = "account.move"

	exclude_from_fiscal_book = fields.Boolean(
		string='Exclude from fiscal book',
		default=False,
		help='Exclude this document from fiscal book.'
	)