# Copyright 2018 Modoolar <info@modoolar.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    password_expiration = fields.Integer(
        related="company_id.password_expiration", readonly=False
    )
    password_minimum = fields.Integer(
        related="company_id.password_minimum", readonly=False
    )
    password_history = fields.Integer(
        related="company_id.password_history", readonly=False
    )
    password_length = fields.Integer(
        related="company_id.password_length", readonly=False
    )
    password_length_max = fields.Integer(
        related="company_id.password_length_max", readonly=False
    )
    password_lower = fields.Integer(related="company_id.password_lower", readonly=False)
    password_upper = fields.Integer(related="company_id.password_upper", readonly=False)
    password_numeric = fields.Integer(
        related="company_id.password_numeric", readonly=False
    )
    password_special = fields.Integer(
        related="company_id.password_special", readonly=False
    )
    password_estimate = fields.Integer(
        related="company_id.password_estimate", readonly=False
    )

    @api.onchange('password_length_max')
    def _onchange_password_length_max(self):
        if self.password_length_max > 0 and self.password_length_max < self.password_length:
            raise ValidationError(_("El número máximo de caracteres no puede ser inferior al número mínimo de caracteres"))
