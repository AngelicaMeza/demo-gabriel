# -*- coding: utf-8 -*-
{
    'name': "sale_customization",
    'summary': """
        Personalización del módulo de Ventas""",
    'description': """
        Personalización del módulo de Ventas
    """,
    'author': "ITSALES",
    'website': "https://www.itsalescorp.com/",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['sale_stock', 'sale_crm', 'sales_team', 'stock_customization'],
    'data': [
        'security/security.xml',
        'security/groups.xml',
        'data/sale_data.xml',
        'views/views_sale_inherit.xml',
        'views/masters.xml',
        'views/templates.xml',
        'reports/saleorder_report.xml',
        'reports/saleorder_report_bs.xml',
        'views/sale_portal_templates.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/stock_move_line.xml',
        'views/stock_warehouse.xml',
    ],
    'qweb': ['static/src/xml/qty_at_date.xml'],
}