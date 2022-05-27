# -*- coding: utf-8 -*-
{
    'name': "external_service",
    'summary': """
        Modulo para Servicio Externo.
    """,
    'author': "IT Sales",
    'category': 'Operations/Field Service',
    'version': '0.1',
    'depends': ['helpdesk_fsm', 'helpdesk_delivery'],

    'data': [
        'security/fsm_security.xml',
        # 'security/ir.model.access.csv',
        'data/sequences.xml',
        'wizard/create_task_views.xml',
        'views/field_service.xml',
        'views/project_views.xml',
        'views/stock_picking_views.xml',
        'views/fsm_task_type_view.xml',
        'views/helpdesk_views.xml',
        'views/project_task_type_view.xml',
    ],
}