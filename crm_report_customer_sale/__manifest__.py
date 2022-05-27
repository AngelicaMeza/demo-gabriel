# -*- coding: utf-8 -*-
{
	'name': "informe cliente",
	'summary': """Informe cliente venta""",
	'description': """informe cliente""",
	'author': "ItSales",
	'website': "http://www.itsalescorp.com",
	'category': 'report',
	'version': '0.1',
	'depends': [
		'account',
		'stock_customization'
	],
	'data': [
		'security/ir.model.access.csv',
		'views/views.xml',
	],
}
