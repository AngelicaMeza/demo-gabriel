# -*- coding: utf-8 -*-
{
    'name': "RIF periodic validation",
    'summary': """
        Validation of the expiration date of the RIF
        """,
    'description': """
        A daily validation of the validity of the rif of the supplier contacts is performed.
    """,
    'author': "ITSale",
    'website': "http://www.itsalecorp.com",
    'category': 'Contact',
    'version': '0.1',
    'depends': ['base', 'mail'],
    'data': [
        'views/res_users.xml',
        'cron/res_partner.xml',
    ],
}