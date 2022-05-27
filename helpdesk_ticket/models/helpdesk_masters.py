# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class HelpdeskChannel(models.Model):
	_name = "helpdesk.channel"
	_order = "sequence"

	name = fields.Char('Nombre del canal', required=True, translate=True)
	sequence = fields.Integer(default=10)
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('name_uniq', 'unique (name)', "El canal ya existe !!!"),
	]

class HelpdeskServiceType(models.Model):
	_name = "helpdesk.service.type"
	_order = "sequence"

	name = fields.Char('Tipo de servicio', required=True, translate=True)
	sequence = fields.Integer(default=10)
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('name_uniq', 'unique (name)', "El tipo de servicio ya existe !!!"),
	]

class HelpdeskAnalytUser(models.Model):
	_name = "helpdesk.analyst.user"
	_rec_name = "user_id"

	user_id = fields.Many2one('res.users', string='Usuario', required=True)
	region_id = fields.Many2one('crm.region', string='Región', required=True, ondelete="restrict")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('technical_uniq', 'unique (user_id, region_id)', "Técnico ya existe !!!"),
	]

class HelpdeskCausal(models.Model):
	_name = "helpdesk.causal"

	name = fields.Char(string='Causal', required=True)
	team_id = fields.Many2one('helpdesk.team', string='Equipo', index=True, required=True)
	code = fields.Integer(string='Codigo', readonly=True, copy=False)
	active = fields.Boolean('Active', default=True)

	@api.model_create_multi
	def create(self, vals_list):
		res = super(HelpdeskCausal, self).create(vals_list)
		for rec in res:
			rec.code = self.env['ir.sequence'].next_by_code('helpdesk.causal')
		return res

	_sql_constraints = [
		('name_code_uniq', 'unique (name, code)', "Causal ya existe !!!"),
	]

class HelpdeskSubStages(models.Model):
	_name = "helpdesk.substage"
	_order = "sequence"

	name = fields.Char(related='stage_id.name')
	sequence = fields.Integer()
	stage_id = fields.Many2one('helpdesk.stage', string='Etapa resolutora', required=True)
	team_id = fields.Many2one('helpdesk.team', string='Atendido en')
	is_close = fields.Boolean(related='stage_id.is_close', string='Etapa de Cierre')
	causal_ids = fields.Many2many('helpdesk.causal', string='Causal(es)')
	user_ids = fields.Many2many('res.users', string='Responsable(s)')
	time_percent = fields.Integer(string='Porcentaje %')

	select_user_id = fields.Selection([
		('user_id', 'Ejecutivo cartera'),
		('region', 'Analista'),
		('custom', 'Personalizado'),
		('N/A', 'Miembros del equipo')],
		string='Asignada a',
		default='N/A',
		required=True
	)
	ticket_type_id = fields.Many2one('helpdesk.ticket.type', string='Requerimiento')

	_sql_constraints = [
		('substage_uniq', 'unique (stage_id, ticket_type_id)', "Exiten etapas resolutoras duplicadas !!!"),
	]

class HelpdeskFailure(models.Model):
	_name = "helpdesk.failure"
	_description = "Describe a failure"

	name = fields.Text(string='Failure', required=True)
	active = fields.Boolean('Active', default=True)

class HelpdeskStageFollowHistory(models.Model):
	_name = "helpdesk.stage.history"
	_description = "save the change between stages"

	substage_id = fields.Many2one('helpdesk.substage', readonly="True", string="Etapa resolutora")
	team_id = fields.Many2one('helpdesk.team', readonly="True", string="Atendido en")
	substage_time = fields.Datetime(readonly="True", string="Fecha limite de etapa resolutora")
	date_assigned = fields.Datetime(readonly="True", string="Fecha de asignación")
	date_reached = fields.Datetime(readonly="True", string="Fecha de ejecución")
	sla_status = fields.Selection(selection=[('reached', 'Alcanzado'), ('failed', 'Fallido'), ('in_progress', 'En proceso')], readonly="True", string="Estado del sla por subetapa")
	execution_time = fields.Float(readonly="True", string='Tiempo de ejecución (horas)')
	history_line_close = fields.Boolean(invisible="True")
	ticket_id = fields.Many2one('helpdesk.ticket', invisible="True", string="Ticket")
