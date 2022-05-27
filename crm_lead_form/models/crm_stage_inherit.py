# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError

class Stage(models.Model):
    _inherit = "crm.stage"

    # identificador unico para las etapas
    stage_code = fields.Integer(string="Código", required=True)
    _sql_constraints=[('stage_code_uniq','UNIQUE (stage_code)','El código de etapa debe ser único'),]

    @api.constrains('stage_code')
    def _check_stage_code(self):
        if self.stage_code > 999 or self.stage_code < 1:
            raise ValidationError('El código no puede ser cero (0) o tener mas de 3 dígitos')
