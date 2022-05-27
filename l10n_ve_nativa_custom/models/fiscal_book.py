from odoo import fields, models, api, exceptions, _

class FiscalBook(models.Model):
    _inherit = 'fiscal.book'

    def reajuste_totales(self):
        base_amount = 0
        tax_amount = 0
        for lin in self.fbl_ids:
            #################################################################################
            if lin.doc_type == 'N/C':
                base_amount -= lin.vat_exempt + lin.vat_general_base + lin.vat_reduced_base + lin.vat_additional_base
                tax_amount -= lin.vat_general_tax + lin.vat_reduced_tax + lin.vat_additional_tax
            else:
                base_amount += lin.vat_exempt + lin.vat_general_base + lin.vat_reduced_base + lin.vat_additional_base
                tax_amount += lin.vat_general_tax + lin.vat_reduced_tax + lin.vat_additional_tax
            ####################################################################################

        self.base_amount = base_amount
        self.tax_amount = tax_amount