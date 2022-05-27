# -*- coding: utf-8 -*-
{
    'name': "Stock Return Lot/Serial Number",
    'summary': """Allow return products with tracking""",
    'description': """Allow return products with tracking selecting its Lot/Serial Number""",
    'author': "ITSales",
    'website': "https://www.itsalescorp.com/",
    'category': 'Stock',
    'version': '1.0',
    'depends': ['stock'],
    'data': [
        'wizard/stock_picking_return_views.xml',
    ],
}