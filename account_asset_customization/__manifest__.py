# -*- coding: utf-8 -*-

{
    'name': "Account asset customization",
    'summary': """
       Add action buttons to confirm asset
    """,
    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",
    'category': 'Accounting/Accounting',
    'version': '0.1',
    'depends': ['account_asset'],
    'data': [
        'wizards/validate_active.xml',
        'wizards/calculate_amortization.xml',
        'views/views.xml',
    ],
}
