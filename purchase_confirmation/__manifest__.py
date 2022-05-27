# -*- coding: utf-8 -*-
{
	'name': "Purchase Confirmation",
	'summary': "",
	'description': "",
	'author': "ITSales",
	'website': "https://www.itsalescorp.com/",
	'category': 'Operations/Purchase',
	'version': '1.0',
	'depends': [
		'purchase_requisition',
		'crm_partner_inherit',
		'hr',
		'user_signature'
	],
	'data': [
		'security/groups.xml',
		'views/purchase_requisition_views.xml',
		'views/purchase_views.xml',
		'views/res_config_settings_views.xml',
		'views/template.xml',
		'report/purchase_order.xml',
		'report/purchase_order_quotation.xml',
		'report/purchase_order_quotation_bs.xml',
		'report/conditions.xml',
		'wizard/purchase_validation.xml',
	],
}