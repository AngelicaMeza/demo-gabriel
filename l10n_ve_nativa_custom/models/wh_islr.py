#from openerp.report import report_sxw
#from openerp.tools.translate import _

from odoo import models, api, _
from odoo.exceptions import UserError, Warning
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RepComprobanteIslr(models.AbstractModel):
    _inherit = 'report.l10n_ve_withholding_islr.template_wh_islr'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            raise UserError(_("Necesita seleccionar una retencion para imprimir."))
        data = {'form': self.env['islr.wh.doc'].browse(docids)}
        res = dict()
        partner_id = data['form'].partner_id
        if partner_id.company_type == 'person':
            if partner_id.nationality == 'V' or partner_id.nationality == 'E':
                document = str(partner_id.nationality) + str(partner_id.identification_id)
            else:
                document = str(partner_id.identification_id)
        else:
            document = partner_id.vat

        if data['form'].state == 'done':
            #######################################################################################################################
            if data['form'].invoice_ids.invoice_id.currency_id != data['form'].invoice_ids.invoice_id.company_id.currency_id:
                total_doc = data['form'].invoice_ids.invoice_id.amount_total_signed * -1
            else:
                total_doc = data['form'].invoice_ids.invoice_id.amount_total
            #######################################################################################################################
            # code_code = ''
            # for code in data['form'].concept_ids.iwdi_id.islr_xml_id:
            #     code_code = code.concept_code
            return {
                'data': data['form'],
                'document': document,
                'total_doc': total_doc,
                # 'code_code': code_code,
                'model': self.env['report.l10n_ve_withholding_islr.template_wh_islr'],
                'doc_model': self.env['report.l10n_ve_withholding_islr.template_wh_islr'],
                'lines': res,  # self.get_lines(data.get('form')),
                # date.partner_id
            }
        else:
            raise UserError(_("La Retencion de ISLR debe estar en estado Realizado para poder generar su Comprobante"))

