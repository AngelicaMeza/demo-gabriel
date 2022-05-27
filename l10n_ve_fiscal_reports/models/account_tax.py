# -*- coding: utf-8 -*-

from odoo import models, fields, _

class AccountTax(models.Model):
	_inherit = 'account.tax'

	tax_type = fields.Selection([
		('exempt', 'Exempt'),
		('untaxed', 'Not subject to taxation'),
		('general', 'General tax'),
		('reduced', 'Reduced tax'),
		('additional', 'Additional tax')],
		string='Tax type',
		help=_("""Allows to identify the tax type for fiscal reports.""")
	)