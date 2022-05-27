# -*- coding: utf-8 -*-
{
	'name': "Stock Reports",
	'summary': """Reports""",
	'description': """Reports from inventory module""",
	'author': "ITSales",
	'website': "https://www.itsalescorp.com/",
	'category': 'Stock',
	'version': '1.0',
	'depends': ['stock_customization', 'report_xlsx'],
	'data': [
		'reports/stock_reports.xml',
		'reports/delivery_order_template.xml',
		'reports/sim_delivery_order_template.xml',
		'views/delivery_guide_view.xml',
		'views/wizard.xml',
		'views/actions.xml',
		'reports/delivery_guide.xml'
	],
}