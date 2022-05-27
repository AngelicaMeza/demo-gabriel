
# coding: utf-8
{
    "name": "Tipo de Persona, Documento de Identidad y Validaciones",
    'summary': """Tipo de persona, Documentos de indentidad y validaciones de estos""",
    "description": """
     Agrega el tipo de persona, y coloca el Documento de Identidad segun el tipo de persona
      y sus respectivos atributos
    """,
    "version": "13",
    'depends': ["base", "base_vat"],
    "author": "It Sales",
    "license": "AGPL-3",
    "website": "www.itsalescorp.com",
    "category": "Localizacion,",
    "data": [
        'security/ir.model.access.csv',
        'views/res_partner_people_type.xml',
        'views/docum_ident_res_partner.xml',
    ],
    "installable": True,
    'application': True,
}
