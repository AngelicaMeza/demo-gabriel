# -*- coding: utf-8 -*-
{
	'name' : 'l10n_ve_fiscal_reports',
	'summary': 'View and download Venezuelan fiscal reports',
	'author': "IT Sales",
	'category': 'Accounting/Accounting',
	'website': 'https://www.itsalescorp.com/',
	'version': '0.1',
	'depends': ['account_reports', 'l10n_ve_withholding_iva'],
	'data': [
		'views/account_fiscal_book_menu.xml',
		'views/account_move_views.xml',
		'views/account_tax_views.xml',
	],
		'license': 'LGPL-3',
}