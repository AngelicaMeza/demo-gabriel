# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AdvancePaymentMethod(models.Model):
    _name = 'advance.payment.method'
    _description = 'Advance Payment Method'

    name = fields.Char()

