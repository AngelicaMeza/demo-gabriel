# -*- coding: utf-8 -*-
{
    'name': "Auth Signup Customization",

    'summary': """
        Add action to the users view view
        """,

    'description': """
        Add a action to send to many users, emails with link to change or set password.
    """,

    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['auth_signup'],

    # always loaded
    'data': [
        'wizard/reset_password_wizard.xml',
        'views/views.xml',
    ],
}
