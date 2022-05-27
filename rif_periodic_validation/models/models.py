# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime, date, timedelta

class Partner(models.Model):
    _inherit = "res.partner"

    def rif_expiration_check(self):
        notification_day = date.today() + timedelta(days=30)
        contacts = self.search([])
        for contact in contacts:
            if (contact.contact_type == '2' or contact.contact_type == '1') and (contact.expired_rif and contact.expired_rif == notification_day): #contact.expired_rif and contact.expired_rif == notification_day:
                self.env['mail.activity'].create({
                'activity_type_id': 6,
                'note': _("El RIF del proveedor vencerá en 30 días, por favor renueve el documento antes de la fecha de expiración."),
                'user_id': self.env['res.users'].search([('rif_notification', '=', True)], limit= 1).id or 2,  #contact.user_id.id,
                'res_id': contact.id,
                'res_model_id': self.env.ref('base.model_res_partner').id,
            })
        
class User(models.Model):
    _inherit = "res.users"

    rif_notification = fields.Boolean()

    @api.constrains('rif_notification')
    def check_only_one(self):
        if len(self.search([('rif_notification', '=', True)])) > 1:
            raise exceptions.ValidationError(_("Solo debe haber un supervisor de proveedores"))


# The supplier\'s RIF will expire in 30 days, please renew the document before the expiration date.
# There should only be one supplier supervisor