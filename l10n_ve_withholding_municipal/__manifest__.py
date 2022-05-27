
# coding: utf-8
{
    "name": "Retencion Municipal Venezuela",
    'summary': """""",
    "description": """
     Crear el grupo usado en la localización
    """,
    "version": "13",
    "depends": ["base_vat", "base", "account", 'l10n_ve_account_fiscal_requirements', 'l10n_ve_base_withholdings'],
    "author": "It Sales",
    "license": "AGPL-3",
    "website": "www.itsalescorp.com",
    "category": "Localizacion,",
    'data': [
        'security/ir.model.access.csv',
        'view/account_invoice_view.xml',
        'view/partner_view.xml',
        'view/wh_muni_view.xml',
        'report/withholding_muni_report.xml',

    ],
    "installable": True,
    'application': True,

}
