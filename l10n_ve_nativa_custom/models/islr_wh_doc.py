# coding: utf-8
##############################################################################
import time

from odoo import api
from odoo import fields, models
from odoo import exceptions
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp


class IslrWhDoc(models.Model):
    _inherit = "islr.wh.doc"
    
    @api.model
    ################################################################
    def _get_journal(self,partner_id=None, invoice_type=None):
        filtro = partner_id
        if not partner_id:
            company = self.env.user.sudo().company_id
            filtro = company.partner_id
        #######################################################
        if invoice_type in ('out_invoice', 'out_refund'):
        ######################################################
            res = filtro.sale_islr_journal_id
        else:
            res = filtro.purchase_islr_journal_id
        if res:
            return res
        else:
            raise exceptions.except_orm(
                _('Configuration Incomplete.'),
                _("No se encuentra un diario para ejecutar la retención ISLR"
                  " automáticamente, cree uno en vendedor/proveedor > "
                  "contabilidad > Diario de retencion ISLR"))

    ###################################################################################
    def name_get(self, ):
        res = []
        for item in self:
            if item.name == '':
                res.append((item.id, 'RET/ISRL'))
            else:
                if item.number and item.state == 'done':
                    res.append((item.id, '%s (%s)' % (item.number, item.name)))
                else:
                    res.append((item.id, '%s' % (item.name)))
        return res
    ###################################################################################
