# -*- coding: utf-8 -*-
{
	'name': "Helpdesk Delivery",
	'summary': "Crea una entrega desde helpdesk",
	'description': """
		Permite crear una tranferencia interna partiendo desde
		la informacion de un ticket de mesa de ayuda.
	""",
	'author': "ITSales",
	'website': "https://www.itsalescorp.com/",
	'version': '1.0',
	'category': 'Operations/Helpdesk',
	'depends': ['helpdesk_ticket', 'stock_stages'],
	'data': [
		'wizard/delivery_wizard.xml',
		'wizard/return_wizard.xml',
		'views/helpdesk_views.xml',
	],
}