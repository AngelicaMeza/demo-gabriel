# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class partner(models.Model):
    _inherit = "res.partner"
    
    portfolio_advisor = fields.Many2one(comodel_name='portfolio.advisor', string="Asesor cartera", ondelete="restrict")
