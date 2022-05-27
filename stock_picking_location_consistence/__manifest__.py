# -*- coding: utf-8 -*-
{
    'name': "Stock Picking Location Consistence",

    'summary': """
        Location consistence between picking and picking lines
        """,

    'description': """
        when the picking location change, the lines location change to
    """,

    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",

    'category': 'Stock',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
}
