# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import models, fields, api
from odoo import _

class Users(models.Model):
    _inherit = "res.users"

    signature_doc = fields.Binary(attachment=True)