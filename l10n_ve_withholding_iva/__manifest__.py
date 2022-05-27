# coding: utf-8
###########################################################################

{
    "name": "Retención IVA las leyes basicas en Venezuela",
    "version": "1.0",
    'author': 'IT Sales',
    "license": "AGPL-3",
    "category": "Localization",
    "website": "www.itsalescorp.com",
    "depends": ['base_vat','base','account','l10n_ve_base_withholdings','web','l10n_ve_location_group'],
    'description' : """
Administración de las retenciones de IVA.
===================================================

Colaborador: Maria Carreño
    """,
    #'website': '',
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_ve_withholding_iva_data.xml',
      #  'wizard/wizard_retention_view.xml',
        'view/generate_txt_view.xml',
        'view/account_invoice_view.xml',
        'view/account_view.xml',
        'view/partner_view.xml',
      # 'view/res_company_view.xml',
        'view/wh_iva_view.xml',
        'report/withholding_vat_report.xml',
    ],
    'installable': True,
    'application': True,
}
