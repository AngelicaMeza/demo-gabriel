# -*- coding: utf-8 -*-
{
    'name': "Base Import Customization",

    'summary': """
        Change base imports""",

    'description': """
    """,

    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_import'],

    'qweb' : ['static/src/xml/base_import.xml'],
}