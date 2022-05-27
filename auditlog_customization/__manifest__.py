# -*- coding: utf-8 -*-
{
    'name': "auditlog customization",

    'summary': """
        Customization of auditlog module
        """,

    'description': """
        
    """,

    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '13',

    # any module necessary for this one to work correctly
    'depends': ['auditlog'],

    # always loaded
    'data': [
        'views/auditlog_view.xml',
        'views/http_request_view.xml',
        'views/http_session_view.xml',
        'data/ir_cron.xml',
    ],
}
