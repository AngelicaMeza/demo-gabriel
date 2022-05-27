# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, exceptions, _

class Partner(models.Model):
    _inherit = "res.partner"

    asigned_orders = fields.Integer()