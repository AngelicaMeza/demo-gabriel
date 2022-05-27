from odoo import api, fields, models

class ImportInherit(models.TransientModel):
    _inherit = 'base_import.import'

    def do(self, fields, columns, options, dryrun=False):
        if 'test_import' not in self._context:
            res = super(ImportInherit, self).with_context(test_import=dryrun).do(fields, columns, options, dryrun)
        else:
            res = super(ImportInherit, self).do(fields, columns, options, dryrun)
        return res