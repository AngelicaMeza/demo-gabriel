# -*- coding: utf-8 -*-
{
    'name': "Formulario de usurario",
    'summary': """
        personalizacion del formulario del usuario""",
    'description': """
        Agrega el maestro de datos asesor cartera
        Añade a las vistas contacto y usuarios los campos pertinentes a este maestro
        Relacion entre el asesor cartera, ejecutivo cartera y contactos
    """,
    'author': "ITSales",
    'website': "http://www.itsalescorp.com",
    'category': 'User',
    'version': '0.1',
    'depends': ['crm_partner_inherit'],
    'data': [
        'security/ir.model.access.csv',
        'views/master.xml',
        'views/res_users.xml',
    ],
}