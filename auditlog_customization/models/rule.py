import copy

from odoo import _, api, fields, models, modules

class AuditlogRule(models.Model):
    _inherit = "auditlog.rule"
    _description = "Auditlog - Rule"

    def _make_create(self):
        """Instanciate a create method that log its calls."""
        self.ensure_one()
        log_type = self.log_type

        @api.model_create_multi
        @api.returns("self", lambda value: value.id)
        def create_full(self, vals_list, **kwargs):
            self = self.with_context(auditlog_disabled=True)
            rule_model = self.env["auditlog.rule"]
            new_records = create_full.origin(self, vals_list, **kwargs)
            # Take a snapshot of record values from the cache instead of using
            # 'read()'. It avoids issues with related/computed fields which
            # stored in the database only at the end of the transaction, but
            # their values exist in cache.
            new_values = {}
            fields_list = rule_model.get_auditlog_fields(self)
            for new_record in new_records.sudo():
                new_values.setdefault(new_record.id, {})
                for fname, field in new_record._fields.items():
                    if fname not in fields_list:
                        continue
                    new_values[new_record.id][fname] = field.convert_to_read(
                        new_record[fname], new_record
                    )
            rule_model.sudo().create_logs(
                self.env.uid,
                self._name,
                new_records.ids,
                "create",
                None,
                new_values,
                {"log_type": log_type},
            )
            return new_records

        @api.model_create_multi
        @api.returns("self", lambda value: value.id)
        def create_fast(self, vals_list, **kwargs):
            self = self.with_context(auditlog_disabled=True)
            rule_model = self.env["auditlog.rule"]
            vals_list2 = copy.copy(vals_list)
            new_records = create_fast.origin(self, vals_list, **kwargs)
            new_values = {}
            for vals, new_record in zip(vals_list2, new_records):
                new_values.setdefault(new_record.id, vals)
            rule_model.sudo().create_logs(
                self.env.uid,
                self._name,
                new_records.ids,
                "create",
                None,
                new_values,
                {"log_type": log_type},
            )
            return new_records

        return create_full if self.log_type == "full" else create_fast

    @api.model
    def get_auditlog_fields(self, model):
        """
        Get the list of auditlog fields for a model
        By default it is all stored fields only, but you can
        override this.
        """    
        return list(
            n
            for n, f in model._fields.items()
            if ((not f.compute and not f.related ) or f.store) and not f.type == 'binary'
        )