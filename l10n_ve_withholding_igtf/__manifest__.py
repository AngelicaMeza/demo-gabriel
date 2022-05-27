{
    'name': "l10n_ve_withholding_igtf",
    'summary': """ Withholding IGTF """,
    'author': "IT Sales",
    'website': 'https://www.itsalescorp.com/',
    'category': 'Accounting/Localizations',
    'version': '0.1',
    'depends': ['account', 'l10n_ve_validation_res_partner'],
    'data': [
        #'security/ir.model.access.csv',
        'views/assets.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'report/invoice_report.xml',
    ],
    'license': 'LGPL-3',
}
