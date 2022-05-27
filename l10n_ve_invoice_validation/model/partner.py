# coding: utf-8

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _validate_fiscal_document(self):
        self.ensure_one()

        if self.type == 'person':
            if bool(self.identificaction_id) is False or (
                self.parent_id and self.parent_id._validate_fiscal_document() or False):
                return False

        if self.type == 'company' and self.people_type_company == 'pjdo':
            if bool(self.vat) is False or (
                self.parent_id and self.parent_id._validate_fiscal_document() or False):
                return False
        
        return True