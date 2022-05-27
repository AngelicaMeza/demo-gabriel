# -*- coding: utf-8 -*-
{
	'name': "HelpDesk Customization",
	'summary': "Personaliaciones al modulo de HelpDesk",
	'description': "Agrega nuevos modelos como canales y tipo de servicio",
	'author': "IT Sales",
	'website': "https://www.itsalescorp.com/",
	'version': '1.0',
	'category': 'Operations/Helpdesk',
	'depends': [
		'helpdesk_stock',
		'stock_customization',
	],
	'data': [
		'security/helpdesk_security.xml',
		'security/ir.model.access.csv',
		'data/helpdesk_sequences.xml',
		'data/actions.xml',
		'views/res_partner.xml',
		'views/helpdesk_masters_views.xml',
		'views/helpdesk_views.xml',
	],
}