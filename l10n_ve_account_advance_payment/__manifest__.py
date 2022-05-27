# -*- coding: utf-8 -*-
{
    'name': "l10n_ve_account_advance_payment",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/account_advance_register.xml',
        'views/account_advance_apply.xml',
        'views/account_move.xml',
        'views/partner_views.xml',
        'views/res_config.xml',
        'report/advance_apply_report.xml',
    ],

}
