# coding: utf-8
import time
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp

from datetime import timedelta, datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ManualGenerateIva(models.Model):
    _name = 'fiscal.book.manual_iva'



    def _compute_vat_rates(self):
        res = {}
        # for item in self.browse(ids):
        #     res[item.id] = {
        #         'vat_reduced_rate': item.vat_reduced_base and
        #                             item.vat_reduced_tax * 100 / item.vat_reduced_base,
        #         'vat_general_rate': item.vat_general_base and
        #                             item.vat_general_tax * 100 / item.vat_general_base,
        #         'vat_additional_rate': item.vat_additional_base and
        #                                item.vat_additional_tax * 100 / item.vat_additional_base,
        #     }
        return res

    iva_ids = fields.Many2one('fiscal.book', string='Retenciones de IVA Manuales')
    invoice_date = fields.Date('Fecha de Factura',required=True)
    retention_date = fields.Date('Fecha del Comprobante de Retencion de IVA')
    company_id = fields.Many2one(
        'res.partner', string='Compañia',  # lambda self: self.env.company.id,
        help="Compañia", required=True)
    export_paper = fields.Char('Nro Planilla de Exportacion', )
    ctrl_number = fields.Char(string='Nro de Control de Factura', size=64, help='',required=True)
    invoice_number = fields.Char(string='Nro de Factura', size=64, help='',required=True)
    total_with_iva = fields.Float('Total con IVA', help="Sub Total of the invoice (untaxed amount) plus"
                                                         " all tax amount of the related taxes")
    vat_exempt = fields.Float("Exento", help="Exempt is a Tax with 0 tax percentage")
    vat_reduced_base = fields.Float("Base Reducido", help="Vat Reduced Base Amount")
    vat_reduced_tax = fields.Float("IVA Reducido", help="Vat Reduced Tax Amount")
    vat_general_base = fields.Float("Base Imponible", help="Vat General Base Amount")
    vat_general_tax = fields.Float("IVA", help="Vat General Tax Amount")
    vat_additional_base = fields.Float("Base Adicional", help="Vat Generald plus Additional Base Amount")
    vat_additional_tax = fields.Float("IVA Adicional", help="Vat General plus Additional Tax Amount")
    get_wh_vat = fields.Float(string="Retención de IVA", help="Retención de IVA")
    wh_number = fields.Char(string='Nro de  Comprobante de Retención', size=64, help="")
    vat_general_rate = fields.Many2one('account.tax', string='Alicuota General', help="Alicuota")
    vat_reduced_rate = fields.Many2one('account.tax', string='Alicuota Reducida', help="Alicuota")
    vat_additional_rate = fields.Many2one('account.tax', string='Alicuota Adicional', help="Alicuota")
    
    # id_tax = fields.Integer('hola')
