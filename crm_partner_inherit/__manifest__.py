# -*- coding: utf-8 -*-
{
    'name': "CRM Plantilla de CLIENTES / PROVEEDORES",

    'summary': """
       Adaptacion de los formularios de Cliente y Proveedor""",

    'description': """
        Adaptacion de los formularios de Cliente y Proveedor, para ser usado por el CRM
    """,

    'author': "It Sales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM/ partner',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'l10n_ve_withholding_iva', 'l10n_ve_withholding_islr', 'l10n_ve_validation_res_partner', 'l10n_ve_account_advance_payment'],

    # always loaded
    'data': [
        'security/crm_partner_inherit_security.xml',
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/masters.xml',
        'views/res_partner_view_form.xml',
        'views/res_partner_account.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
