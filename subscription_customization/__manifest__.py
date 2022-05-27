# -*- coding: utf-8 -*-
{
    'name': "Subscription customization",
    'summary': """
        Subscription module customization """,
    'description': """
        Subscription module customization
    """,
    'author': "ITSales",
    'website': "https://www.itsalescorp.com/",
    'category': 'Subscription',
    'version': '0.1',
    'depends': ['sale_subscription', 'sale_customization'],
    'data': [
        'views/views.xml',
        'views/stock_picking.xml',
        'security/groups.xml',
    ],
}