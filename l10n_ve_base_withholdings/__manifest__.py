{
    "name": "Gestión de retenciones leyes venezolanas",
    "version": "1.0",
    'author': 'IT Sales',
    "license": "AGPL-3",
    "category": "Localization",
    "website": "www.itsalescorp.com",
    "depends": [ 'account',
        'base_vat',
        'account_accountant', 'base', 'l10n_ve_account_fiscal_requirements','l10n_ve_location_group'],
    'data': [
        'security/ir.model.access.csv',
        'view/base_withholding_view.xml',
    ],
    'installable': True,
    'application': True,
}
