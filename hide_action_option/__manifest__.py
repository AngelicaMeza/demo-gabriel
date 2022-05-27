# -*- coding: utf-8 -*-
{
    'name': "Hide Action Options",

    'summary': """
        Hide some options in the action options""",

    'description': """
        Hide delete option
        Hide change password option
    """,

    'author': "ITSales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    'qweb': ['static/src/xml/template.xml'],
    # always loaded
    'data': [
        'security/groups.xml',
        'views/views.xml',
        'views/assets.xml',
    ],
}
