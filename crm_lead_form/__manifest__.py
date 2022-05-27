# -*- coding: utf-8 -*-
{
    'name': "Formulario de oportunidades",

    'summary': """
        Personalización de las oportunidades""",

    'description': """
        Personalización del formulario de oportunidades y el flujo que siguen las mismas, 
​        permitiendo el seguimiento de la etapas y la creación de presupuestos de alquiler.
        aumentando la relación que se guarda con lo presupuestos relacionados para la realización
        de acciones automáticas y restricciones en el flujo.
    """,

    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",
    'category': 'CRM',
    'version': '0.1',
    'depends': [
        'crm',
        'sale_crm',
        'crm_partner_inherit',
    ],
    'data': [
        'data/sequence.xml',
        'security/crm_lead_form_security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/mail_template.xml',
        'views/views.xml',
        'data/actions.xml',
        'views/masters.xml',
        'wizard/crm_lead_lost_views.xml',
    ],
}
