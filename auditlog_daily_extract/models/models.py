# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DailyExtract(models.TransientModel):
    _name = "daily.extract"
    _description = "Daily extract"

    def extract_table(self):
        query="COPY (SELECT model.name AS Modelo, field.name AS Campo, audit_line.old_value_text AS Valor_anterior, audit_line.new_value_text AS Valor_nuevo, partner.name AS Usuario, audit_log.create_date AS Fecha FROM public.auditlog_log_line as audit_line JOIN public.auditlog_log as audit_log on audit_log.id = audit_line.log_id JOIN public.ir_model as model on model.id = audit_log.model_id JOIN public.ir_model_fields as field on field.id = audit_line.field_id JOIN public.res_users as users on users.id = audit_log.user_id JOIN public.res_partner as partner on partner.id = users.partner_id where audit_log.create_date >= '2022-02-20' and audit_log.create_date < '2022-02-21' ) TO '/tmp/registros_20-02-22.csv' WITH CSV HEADER;"
        self._cr.execute(query)