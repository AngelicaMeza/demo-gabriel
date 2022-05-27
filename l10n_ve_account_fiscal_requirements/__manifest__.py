# coding: utf-8

{
    'name': 'Requerimientos Fiscales Venezuela',
    'version' : '1.0',
    'author': 'IT Sales',
    "license": "AGPL-3",
    "category": "Localization",
    "website": "www.itsalescorp.com",
    'description' : """

 Agrega los requerimientos fiscales exigidos por las leyes venezolanas
 
Colaborador: Maria Carreño
    """,

    'depends': [
        'account',
        'base_vat',
        'account_accountant',
        'l10n_ve_location_group'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_ut_data.xml',
        'data/l10n_ve_account_fiscal_data.xml',
        'wizard/search_info_partner_seniat.xml',
        'wizard/wizard_nro_ctrl_view.xml',
        'view/res_company_view.xml',
        'view/l10n_ut_view.xml',
        'view/account_tax_view.xml',
        'view/account_invoice_view.xml',
        'view/nro_ctrl_secuencial_customer.xml',
    ],
    'installable': True,
    'application': True,
}

