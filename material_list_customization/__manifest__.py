# -*- coding: utf-8 -*-
{
    'name': "material list customization",
    'summary': """Add the product to be manufactured in the bill of materials""",
    'description': """Add the product to be manufactured in the bill of materials""",
    'author': "ItSales",
    'website': "https://www.itsalescorp.com/",
    'category': 'Production',
    'version': '1.0',
    'depends': ['mrp', 'stock_customization'],
    'data': [
        'views/views.xml',
        'views/deconfiguration.xml',
    ],
}