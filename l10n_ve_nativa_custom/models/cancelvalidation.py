
# coding: utf-8
###########################################################################

import time
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    
    
    def button_draft(self):
        flag = 0
        message = 'Hace falta cancelar los siguientes documentos:'
        if self.wh_iva_id:
            
            if self.wh_iva_id.state ==  'draft':
                self.wh_iva_id.action_cancel()
                self.update({'wh_iva_id': False})
                document = ""
            else:    
                flag = 1
                document = "Retencion de IVA:" + str(self.wh_iva_id.name)
            message = message + "  \n " + document
        
        if self.islr_wh_doc_id:
            flag = 1
            document = "Retencion de ISLR:" + str(self.islr_wh_doc_id.name)
            message = message + "  \n " + document
        
        for line in self.debit_note_ids:
            if line.state != 'cancel':
                flag = 1
                document = 'Notas de debito: ' + str(line.name)
                message = message + "  \n " + document

        for line in self.reversal_move_id:
            if line.state != 'cancel':
                flag = 1
                document = 'Factura Rectificativa: ' + str(line.name)
                message = message + "  \n " + document
       

        if flag == 1:
            raise ValidationError(message)
        else:
            finish = super(AccountMove, self).button_draft()
            self.update({'wh_iva': False})
            return  finish


    def action_cancel_retention(self):
        """ Call cancel_move and return True"""
        if self.state == 'posted':
            if self.wh_muni_id: self.wh_muni_id._reverse_moves([{'date': fields.Date.today(), 'ref': _('Reversión %s' % self.wh_muni_id.name)}], cancel=True)
            if self.invoice_id: self.invoice_id.write({'wh_muni_id': False})
            self.write({'state': 'cancel'})
        else:
            raise ValidationError(_("""La retencion debe estar en estado Publicado para poder ser cancelada"""))
        return True