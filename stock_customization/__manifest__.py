# -*- coding: utf-8 -*-
{
    'name': "stock_customization",
    'summary': """Stock customization""",
    'description': """Inventory module customization""",
    'author': "ItSales",
    'website': "https://www.itsalescorp.com/",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['stock', 'crm_lead_form'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/access.xml',
        'data/stock_sequences.xml',
        'data/product_type.xml',
        'views/assets.xml',
        'views/masters.xml',
        'views/product_template_views.xml',
        'views/stock_inherit.xml',
        'views/stock_quant_views.xml',
        'views/stock_scrap_views.xml',
        'views/warehouse.xml',
    ],
}