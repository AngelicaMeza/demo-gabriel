

# -*- coding: UTF-8 -*-
{
    "name": "Correcciones de ventas y compras",
    'summary': """Validaciones para Rif y email en compa;ia""",
    "description": """
    Correcciones de ventas y compras; rif, tipo de documento y Documento de Identidad
    """,
    "version": "13",
    "depends": [
        "sale",
        "purchase",
        "base",
        "base_vat",
        "l10n_ve_validation_res_partner",
        "l10n_ve_validation_rif_res_company"
    ],
    "author": "It Sales",
    "license": "AGPL-3",
    "website": "www.itsalescorp.com",
    "category": "Localizacion,",
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order_innherit.xml',
        'views/purchase_order_innherit.xml',
    ],
    "installable": True,
    'application': True,
}