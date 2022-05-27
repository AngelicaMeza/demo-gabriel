# -*- coding: utf-8 -*-
{
    'name': "Quality customization",

    'summary': """
        Customization of the quality module""",

    'description': """
        Adds lists of items to be checked in the quality verification process.
        The quality verification process is performed depending on the type of product follow up.
    """,

    'author': "ITSales",
    'website': "http://www.itsalescorp.com",

    'category': 'Manufacturing/Quality',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['quality_mrp_workorder'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/masters.xml',
        'views/quality_check.xml',
        'views/mrp_workorder.xml',
    ],
}
