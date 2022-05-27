# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from collections.abc import Mapping

INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')

class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):


        for move in self:
            if (move.restrict_mode_hash_table and move.state == "posted" and set(vals).intersection(INTEGRITY_HASH_MOVE_FIELDS)):
                raise UserError(_("You cannot edit the following fields due to restrict mode being activated on the journal: %s.") % ', '.join(INTEGRITY_HASH_MOVE_FIELDS))
            if (move.restrict_mode_hash_table and move.inalterable_hash and 'inalterable_hash' in vals) or (move.secure_sequence_number and 'secure_sequence_number' in vals):
                raise UserError(_('You cannot overwrite the values ensuring the inalterability of the accounting.'))
            if (move.name != '/' and 'journal_id' in vals and move.journal_id.id != vals['journal_id']):
                raise UserError(_('You cannot edit the journal of an account move if it has been posted once.'))

            # You can't change the date of a move being inside a locked period.
            if 'date' in vals and move.date != vals['date']:
                move._check_fiscalyear_lock_date()
                move.line_ids._check_tax_lock_date()

            # You can't post subtract a move to a locked period.
            if 'state' in vals and move.state == 'posted' and vals['state'] != 'posted':
                move._check_fiscalyear_lock_date()
                move.line_ids._check_tax_lock_date()

        if self._move_autocomplete_invoice_lines_write(vals):
            res = True
        else:

            # Agregar concept_id al correspondiente apunte contable de cada linea de factura
          
            #1). Localizar el correspondiente apunte contable de cada linea de factura
            if 'invoice_line_ids' in vals:
                for val in vals['invoice_line_ids']:
                    pos = 0
                    while (val[1] != vals['line_ids'][pos][1]) and (pos < len(vals['line_ids'])):
                        pos += 1

                    # 2). Agregar concept_id en el apunte contable localizado
                    if isinstance(val[2], Mapping) and ('concept_id' in val[2]):
                        if not vals['line_ids'][pos][2]:
                            vals['line_ids'][pos][2] = {'concept_id' : val[2]['concept_id']}
                        else:
                            vals['line_ids'][pos][2]['concept_id'] = val[2]['concept_id']
            #vals.pop('invoice_line_ids', None)
            res = super(AccountMove, self.with_context(check_move_validity=False)).write(vals)

        # You can't change the date of a not-locked move to a locked period.
        # You can't post a new journal entry inside a locked period.
        if 'date' in vals or 'state' in vals:
            self._check_fiscalyear_lock_date()
            self.mapped('line_ids')._check_tax_lock_date()

        if ('state' in vals and vals.get('state') == 'posted') and self.restrict_mode_hash_table:
            for move in self.filtered(lambda m: not(m.secure_sequence_number or m.inalterable_hash)):
                new_number = move.journal_id.secure_sequence_id.next_by_id()
                vals_hashing = {'secure_sequence_number': new_number,
                                'inalterable_hash': move._get_new_hash(new_number)}
                res |= super(AccountMove, move).write(vals_hashing)

        # Ensure the move is still well balanced.
        if 'line_ids' in vals:
            if self._context.get('check_move_validity', True):
                self._check_balanced()
            self.update_lines_tax_exigibility()

        return res
