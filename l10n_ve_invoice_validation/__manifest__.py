# coding: utf-8
###########################################################################

##############################################################################
{
    "name": "Facturacion-validaciones y correcciones; números de control automaticos Clientes-Proveedores",
    'version': '1.0',
    'author': 'IT Sales',
    "category": "Localization",
    "website": "www.itsalescorp.com",
    "depends": [
        "account",
		"sale",
        "base",
        "base_vat",
        "l10n_ve_validation_res_partner",
        "l10n_ve_validation_rif_res_company",
    ],
    'demo': [
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/invoice_view.xml',
    ],
    'test': [

    ],
    "installable": True,
    'application': True,
}
