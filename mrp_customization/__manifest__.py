# -*- coding: utf-8 -*-
{
    'name': "mrp_customization",
    'summary': """ MRP Custom """,
    'author': "IT Sales",
    'category': 'Manufacturing/Manufacturing',
    'version': '0.1',
    'depends': ['stock_customization'],
    'data': [
        'security/mrp_security.xml',
        'security/ir.model.access.csv',
        'views/masters.xml',
        'views/mrp_production_views.xml',
        'wizard/request_keys.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_workorder_views.xml',
        'views/res_users_views.xml',
    ],
}