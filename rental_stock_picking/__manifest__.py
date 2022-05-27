# -*- coding: utf-8 -*-
{
	'name': "Rental Picking",
	'summary': """Allow to create a stock picking to rental products""",
	'description': """Allow to create a stock picking to rental products""",
	'author': "ITSales",
	'website': "http://www.itsalescorp.com",
	'category': 'Sales/Sales',
	'version': '1.0',
	'depends': ['sale_stock_renting'],
	'data': [
		'views/sale_views.xml',
		'views/stock_views.xml',
		'wizard/rental_configurator_views.xml'
	],
}