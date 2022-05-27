# coding: utf-8
##############################################################################
from odoo import api
from odoo import fields, models
from odoo import exceptions
from odoo.tools.translate import _

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _create_islr_wh_doc(self):
        """ Function to create in the model islr_wh_doc
        """
        context = dict(self._context or {})
        ids = isinstance(self.ids, (int)) and [self.ids] or self.ids

        wh_doc_obj = self.env['islr.wh.doc']
        rp_obj = self.env['res.partner']

        acc_part_id = rp_obj._find_accounting_partner(self.partner_id)
        if not (self.type in ('out_invoice', 'in_invoice','in_refund') and rp_obj._find_accounting_partner(self.company_id.partner_id).islr_withholding_agent):
            return True

        context['type'] = self.type
        ###############################################################
        if self.type != 'out_invoice':
            wh_ret_code = wh_doc_obj.retencion_seq_get(self.type)
        else:
            wh_ret_code = ''
        ###############################################################

        if wh_ret_code or self.type == 'out_invoice':
            ######################################################################
            journal = wh_doc_obj._get_journal(self.partner_id, self.type)
            #######################################################################

            acc_part_id = rp_obj._find_accounting_partner(self.partner_id)
            if self.type in ('out_invoice', 'out_refund'):
                acc_id = acc_part_id.property_account_receivable_id.id
                wh_type = 'out_invoice'
            else:
                acc_id = acc_part_id.property_account_payable_id.id
                wh_type = 'in_invoice'
            values = {
                'name': wh_ret_code, #TODO (REVISAR)_('IVA WH - ORIGIN %s' %(inv_brw.number)),
                'partner_id': acc_part_id.id,
             #   'period_id': row.period_id.id,
                'account_id': acc_id,
                'type': self.type,
                'journal_id': journal.id,
                'date_uid': self.date,
                'company_id': self.company_id.id,
                'date_ret':self.date
            }
            if self.company_id.propagate_invoice_date_to_income_withholding:
                values['date_uid'] = self.date_invoice

            islr_wh_doc_id = wh_doc_obj.create(values)
            iwdi_id = self._create_doc_invoices(islr_wh_doc_id)

            self.env['islr.wh.doc'].compute_amount_wh([islr_wh_doc_id])


            if self.company_id.automatic_income_wh is True:
                wh_doc_obj.write(
                                 {'automatic_income_wh': True})
        else:
            raise exceptions.except_orm(_('Invalid action !'), _(
                "No se ha encontrado el numero de secuencia!"))

        return islr_wh_doc_id

    