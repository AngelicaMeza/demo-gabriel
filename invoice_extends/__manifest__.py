# -*- coding: utf-8 -*-
{
    'name': "Extensión de la factura de cliente",
    'summary': """
        Personalización de la factura de cliente
        """,
    'description': """
        Personalización del formato Agregado de campos
    """,
    'author': "ITSales",
    'website': "http://www.itsalescorp.com",
    'category': 'Account',
    'version': '0.1',
    'depends': ['base', 'web', "account"],
    'data': [
        'report/report_invoice_extends.xml',
    ],
}