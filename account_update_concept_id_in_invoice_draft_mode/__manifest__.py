# -*- coding: utf-8 -*-
{
    'name': "account_update_concept_id_in_invoice_draft_mode",

    'summary': """
        Actualizar el Concepto de Islr al editar una factura en borrador""",

    'description': """
        Actualizar el Concepto de Islr al editar una factura en borrador""",

    'author': "ITSALES",
    'website': "https://www.itsalescorp.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
