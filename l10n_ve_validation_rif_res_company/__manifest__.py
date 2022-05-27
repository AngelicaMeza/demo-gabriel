# -*- coding: UTF-8 -*-
{
    "name": "Validaciones de Rif y Compania",
    'summary': """Validaciones para Rif y email en compa;ia""",
    "description": """
    Modifica campo y realiza validaciones al campo vat y al email 
    para hacer las validaciones respectivas que amplican al entornoVenezolano.
    """,
    "version": "13",
    'depends': [
        "base", "base_vat", "l10n_ve_validation_res_partner"],
    "author": "It Sales",
    "license": "AGPL-3",
    "website": "www.itsalescorp.com",
    "category": "Localizacion,",
    "data": [
        'security/ir.model.access.csv',
        'views/l10n_ve_validation_res_company_rif.xml',
   	    'views/l10n_ve_validation_res_partner.xml',
    ],
    "installable": True,
    'application': True,
}
