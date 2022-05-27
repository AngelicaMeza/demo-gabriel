# -*- coding: utf-8 -*-
{
	'name': "Stock Access Rights",
	'summary': """Stock access rights""",
	'description': """Inventory module to manager access rights""",
	'author': "IT Sales",
	'website': "https://www.itsalescorp.com/",
	'category': 'Stock',
	'version': '1.1',
	'depends':  ['stock'],
	'data': [
		'security/access_rules.xml',
		'security/ir.model.access.csv',
		'views/stock_warehouse_views.xml',
		'views/res_users_views.xml',
	],
}