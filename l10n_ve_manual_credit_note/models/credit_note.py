# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DebitNote(models.Model):
    _inherit = 'account.move'

    credit_note_number = fields.Char('Numero de Factura Afectada')
    credit_note_date = fields.Date('Fecha de Factura Afectada')
