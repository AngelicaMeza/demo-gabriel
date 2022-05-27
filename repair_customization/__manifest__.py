# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'Repair Customization',
	'version': '1.0',
	'category': 'Manufacturing/Manufacturing',
	'summary': 'Repair damaged products',
	'description': """""",
	'depends': ['helpdesk_ticket', 'helpdesk_repair'],
	'data': [
		'views/helpdesk_views.xml',
		'views/repair_views.xml',
		'views/stock_location_views.xml',
	],
}