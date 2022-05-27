#-*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

from odoo.osv import query

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # replace constraint to avoit the restriction
    _sql_constraints = [
        ('unique_number', 'unique(sanitized_acc_number, partner_id,company_id)', 'Account Number must be unique'),
    ]
