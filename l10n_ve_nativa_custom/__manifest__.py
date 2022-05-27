# -*- coding: utf-8 -*-
{
    'name': "l10n ve nativa custom",
    'summary': """ Customization for Venezuela's localization """,
    'description': """ Customization for Venezuela's localization """,
    'author': "IT Sales",
    'website': "https://www.itsalescorp.com/",
    'category': 'l10n_ve',
    'version': '13',
    'depends': ['account', 'l10n_ve_withholding_iva', 'l10n_ve_withholding_islr', 'l10n_ve_fiscal_book'],
    'data': [
        "security/ir.model.access.csv",
        'views/views.xml',
    ],
}
