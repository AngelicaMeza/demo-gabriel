# -*- coding: utf-8 -*-
{
	'name': "Account customization",
	'summary': """Personalización del módulo de contabilidad""",
	'description':
	"""
		Personalización del módulo de contabilidad
		Coloca los campos "analytic_account_id" y "analytic_tag_ids" en facturas de contabilidad como requeridos
		Agrega el sello y firma de la empresa en las retenciones
		Agrega documentos a las facturas de proveedores 
	""",
	'author': "ITSales",
	'website': "https://www.itsalescorp.com/",
	'category': 'Accounting/Accounting',
	'version': '1.0',
	'depends': ['account', 'crm_lead_form'],
	'data': [
		'views/account_move.xml',
		'views/change_credit_note_wizard.xml',
		'reports/withholding_vat_report.xml',
		'reports/wh_islr_report.xml',
		'wizards/compute_amount_action.xml',
		'views/actions.xml',
	],
}
