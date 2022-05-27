# -*- coding: utf-8 -*-
{
    'name': "stock_landed_cost_customization",

    'summary': """
        Make visible landed cost elements for account users""",

    'description': """
        Make visible:
        -landed cost check in invoice line
        -create landed cost button in invoice
        -smart button to landed cost lines
    """,

    'author': "ITSales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Operations/Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock_landed_costs'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
}
