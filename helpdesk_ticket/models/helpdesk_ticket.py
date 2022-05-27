# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.helpdesk.models.helpdesk_ticket import HelpdeskTicket as HDT

class HelpdeskTicketType(models.Model):
	_inherit = 'helpdesk.ticket.type'

	name = fields.Char('Nombre del requerimiento', translate=False, required=True)
	service_type = fields.Many2one('helpdesk.service.type', string='Tipo de servicio', required=True)
	team_id = fields.Many2one('helpdesk.team', string='Equipo de Area Resolutora', required=True)
	template_id = fields.Many2one('mail.template', 'Plantilla de correo electrónico', help="""Plantilla de correo electrónico que será enviada al cliente únicamente en etapa(s) de cierre.""")
	user_ids = fields.Many2many('res.users', string='Responsable(s)', index=True)
	
	failure = fields.Boolean('Incluye fallas')
	devices = fields.Boolean('Incluye equipo(s) y serial(es)')
	include_affiliated = fields.Boolean(string='Incluye Afiliado a Incorporar') # añadido by Carlos
	stage_id = fields.Many2one('helpdesk.stage', string='Etapa', help="""Etapa principal que contemplara las etapas resolutoras del requerimiento.""")
	
	description = fields.Text('Descripción', required=True)
	excluded_cluster_ids = fields.Many2many('segmentation.cluster', string='Cluster no aplica', required=True, ondelete="restrict")
	excluded_negotiation_type_id = fields.Many2many('crm.negotiation', string='Modelo de negocio no aplica', ondelete="restrict")
	substage_ids = fields.One2many('helpdesk.substage', 'ticket_type_id', string='Etapa resolutora')
	active = fields.Boolean('Active', default=True)

	select_user_id = fields.Selection([
		('user_id', 'Ejecutivo cartera'),
		('region', 'Analista'),
		('custom', 'Personalizado'),
		('N/A', 'Miembros del equipo')],
		string='Asignada a',
		default='N/A',
		required=True
	)
	
	substage_unit = fields.Selection([
		('percent', 'Porcentaje'),
		('N/A', 'N/A')],
		string='Distribución de tiempo',
		default='N/A',
	)

	_sql_constraints = [
		('name_uniq', 'unique (name)', 'El requerimiento ya existe !!!'),
	]

	@api.constrains('substage_ids', 'substage_unit')
	def _constraint_time_substage_ids(self):
		if self.substage_ids and self.substage_unit == 'percent' and sum(self.substage_ids.mapped('time_percent')) != 100:
			raise ValidationError(_("""La distribucion de porcentaje en las etapas resolutoras debe alcanzar el 100%."""))

	@api.constrains('select_user_id', 'user_ids')
	def _constraint_user_ids(self):
		if self.select_user_id == 'custom' and not self.user_ids:
			raise ValidationError(_("""For custom assign you must select at least one user."""))


class HelpdeskTicket(models.Model):
	_inherit = 'helpdesk.ticket'

	#requirement
	channel_id = fields.Many2one('helpdesk.channel', string="Canal de atención", required=True, tracking=True)
	service_type = fields.Many2one('helpdesk.service.type', string="Tipo de servicio", required=True, tracking=True)
	ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket Type", required=True, tracking=True)
	team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team', index=True, readonly=True)
	req_description = fields.Text(related='ticket_type_id.description')
	include_failure = fields.Boolean(related='ticket_type_id.failure')
	include_devices = fields.Boolean(related='ticket_type_id.devices')
	include_affiliated = fields.Boolean(related='ticket_type_id.include_affiliated')
	failure = fields.Many2many('helpdesk.failure', string='Fallas', ondelete='restrict')

	#stages
	stage_id = fields.Many2one('helpdesk.stage', string='Stage', ondelete='restrict', tracking=True, group_expand='_read_group_stage_ids', copy=False, index=True, domain="[('team_ids', '=', team_id), ('is_sub_stage', '=', False)]")
	substage_id = fields.Many2one('helpdesk.substage', string='Etapa resolutora', tracking=True)
	substages = fields.One2many(related='ticket_type_id.substage_ids')
	show_substages = fields.Boolean(copy=False)
	substage_time = fields.Datetime('Fecha límite de etapa resolutora', readonly=True)
	is_close_stage = fields.Boolean(related='stage_id.is_close')
	date_reached = fields.Datetime('Fecha alcanzada', readonly=True, help="Fecha de cierre del ticket")
	stage_history = fields.One2many('helpdesk.stage.history', 'ticket_id', copy=False, string="Historial de fechas")
	final_sla_status = fields.Selection(selection=[('reached', 'Alcanzado'), ('failed', 'Fallido'), ('ongoing', 'En proceso')], readonly="True", string="Estado de SLA final")
	go_back = fields.Boolean(invisible="True")
	total_time = fields.Float(string="Tiempo de Ejecución Total (horas)", compute="_set_total_time")

	#partner INFO
	partner_id = fields.Many2one(required=True, tracking=True)
	partner_name = fields.Char(related='partner_id.name')
	affiliated = fields.Char(string="Numero de afiliación", required=True)
	vat = fields.Char(string='RIF', required=True)
	cluster_id = fields.Many2one('segmentation.cluster', string='Cluster', readonly=True, ondelete="restrict")
	region_id = fields.Many2one(related="partner_id.region_id")
	portfolio_user = fields.Many2one(string='Ejecutivo cartera', related='partner_id.user_id')
	denomination = fields.Char(related='partner_id.denomination')
	address = fields.Char(related='partner_id.contact_address')
	phone_one = fields.Char(related='partner_id.phone_one')
	phone_two = fields.Char(related='partner_id.phone_two')
	phone_three = fields.Char(related='partner_id.phone_three')
	bank_ids = fields.One2many(related='partner_id.bank_ids')
	status_customer = fields.Selection(related='partner_id.status_customer')
	regional_manager = fields.Many2one(related='partner_id.regional_manager')

	#product
	product_lot = fields.Many2one('stock.production.lot', string='Equipo')
	product_id = fields.Many2one(related='product_lot.product_id')
	product_condition_id = fields.Many2one(related='product_lot.condition_id')
	product_status_id = fields.Many2one(related='product_lot.status_id')
	product_key_version = fields.Many2one(related='product_lot.key_version')
	product_sim_card = fields.Many2one(related='product_lot.sim_card')
	product_network_operator_id = fields.Many2one(related='product_lot.network_operator_id')
	product_negotiation_type_id = fields.Many2one(related='product_lot.negotiation_type_id')
	product_communication_id = fields.Many2many(related='product_lot.communication_id')

	#causal
	causal_id = fields.Many2one('helpdesk.causal', string='Causal', tracking=True, ondelete='restrict')
	causal_substage_ids = fields.Many2many(related='substage_id.causal_ids')
	there_is_causal = fields.Boolean(default=False)

	#user_id
	user_domain = fields.Many2many('res.users', string='User domain')

	#Affiliated Contact Fields
	affiliated_partner_id = fields.Many2one('res.partner', string='Cliente a incorporar')
	affiliated_affiliated_number = fields.Char(string="Numero de afiliación a incorporar")
	affiliated_vat = fields.Char(string='RIF a incorporar')
	affiliated_address = fields.Char(related='affiliated_partner_id.contact_address')
	affiliated_phone_one = fields.Char(related='affiliated_partner_id.phone_one')
	affiliated_phone_two = fields.Char(related='affiliated_partner_id.phone_two')
	affiliated_phone_three = fields.Char(related='affiliated_partner_id.phone_three')
	affiliated_portfolio_user = fields.Many2one(related='affiliated_partner_id.user_id')

	###############################################################################################
	#SETS
	###############################################################################################
	@api.onchange('ticket_type_id')
	def _set_team_id(self):
		"""Asigna area resolutora al seleccionar el requerimiento"""
		if self.ticket_type_id:
			self.team_id = self.ticket_type_id.team_id
			self.user_id, self.user_domain = self._determine_user_to_assign(self.ticket_type_id.select_user_id, self.ticket_type_id.user_ids)

	@api.onchange('team_id')
	def _onchange_team_id(self):
		"""Se sobreescribe la funcion original para que no asigne ningun usuario"""
		if self.team_id and (not self.stage_id or self.stage_id not in self.team_id.stage_ids):
			self.stage_id = self.team_id._determine_stage()[self.team_id.id]

	def _determine_user_to_assign(self, type, members=False):
		user_id = domain = False
		if type == 'N/A':
			if self.user_id.id in self.team_id.member_ids.ids:
				user_id = self.user_id
			else:
				user_id = self.team_id._determine_user_to_assign()[self.team_id.id]
			domain = self.team_id.member_ids.ids
		elif type == 'user_id':
			user_id = self.partner_id.user_id
			domain = self.partner_id.user_id.ids
		elif type in ['region', 'custom']:
			member_ids = []
			if type == 'region':
				member_ids = self.env['helpdesk.analyst.user'].search([('region_id','=',self.partner_id.region_id.id)]).mapped('user_id').ids
			elif type == 'custom' and members:
				member_ids = members.ids
			
			if member_ids and self.user_id.id not in member_ids:
				ticket_count_data = self.env['helpdesk.ticket'].read_group([('stage_id.is_close', '=', False), ('user_id', 'in', member_ids), ('team_id', '=', self.team_id.id)], ['user_id'], ['user_id'])
				open_ticket_per_user_map = dict.fromkeys(member_ids, 0)  # dict: user_id -> open ticket count
				open_ticket_per_user_map.update((item['user_id'][0], item['user_id_count']) for item in ticket_count_data)
				user_id = self.env['res.users'].browse(min(open_ticket_per_user_map, key=open_ticket_per_user_map.get))
			else:
				user_id = self.user_id

			domain = member_ids

		return user_id, domain

	###############################################################################################
	#CLEAN
	###############################################################################################
	@api.onchange('service_type')
	def _onchange_clean_service_type(self):
		"""
			Limpia los campos de 'requerimiento', 'descripcion'
			y 'asignado a' al cambiar el tipo de servicio
		"""
		self.ticket_type_id = False
		self.req_description = False
		self.team_id = False,
		self.user_id = False

	def _clean_ticket(self):
		self.partner_id = False
		self.affiliated = False
		self.cluster_id = False
		self.partner_email = False
		self.channel_id = False
		self.service_type = False
		self.ticket_type_id = False
		self.req_description = False
		self.team_id = False
		self.user_id = False
		self.description = False
		self.failure = False
		self.product_lot = False
		self.affiliated_partner_id = False
		self.affiliated_affiliated_number = False
		self.affiliated_vat = False
		if not self.is_partner_search:
			self.vat = False

	###############################################################################################
	#SEARCH
	###############################################################################################
	search_contact = fields.Many2one('res.partner', string="Contacto RIF", copy=False)
	is_partner_search = fields.Boolean(copy=False)

	@api.onchange('search_contact')
	def set_partner(self):
		if self.search_contact and self.search_contact != self.partner_id:
			self.partner_id = self.search_contact
	
	@api.onchange('partner_id')
	def _search_by_partner(self):
		"""Busca cliente por nombre"""
		if self.partner_id:
			self.affiliated = self.partner_id.affiliated
			self.vat = self.partner_id.vat
			self.cluster_id = self.partner_id.cluster_id
			self.channel_id = False
			self.service_type = False
			self.description = False
			self.failure = False
			self.product_lot = False
			self.affiliated_partner_id = False
			self.affiliated_affiliated_number = False
			self.affiliated_vat = False
		else:
			self._clean_ticket()
	
	@api.onchange('affiliated')
	def _search_by_affiliated(self):
		"""Busca cliente por afiliado"""
		if self.affiliated:
			partner_id = self.env['res.partner'].search([('affiliated', '=', self.affiliated), ('contact_type', 'in', ['0','1'])], limit=1)
			if partner_id:
				self.partner_id = partner_id
			else:
				self._clean_ticket()
				return {
					'warning': {
						'title': 'Alerta',
						'message': _("""El número de afiliado no pertenece a ningún contacto.""")
					}
				}
		else:
			self._clean_ticket()

	@api.onchange('vat')
	def _search_by_vat(self):
		"""Busca cliente por RIF"""
		if self.vat:
			if not self._context.get('import_file', False):
				cr = self._cr
				query = """SELECT id, affiliated FROM public.res_partner WHERE vat = '{}' AND contact_type IN ('0', '1');""".format(self.vat)
				cr.execute(query)
				partner_ids = cr.fetchall()

				if partner_ids:
					if len(partner_ids) == 1:
						self.partner_id = partner_ids[0][0]
						self.search_contact = False
						self.is_partner_search = False

					elif self.partner_id.vat != self.vat:
						# self.partner_id = False
						# self.affiliated = False
						self.is_partner_search = True
						self._clean_ticket()
						return {
							'domain':{
								'search_contact':[('vat', '=', self.vat)]
							},
							'warning': {
								'title': 'Alerta',
								'message': _("""El RIF ingresado pertenece a varios contactos, por favor seleccione el deseado en el campo 'Contacto RIF'.""")
							}
						}
				else:
					self._clean_ticket()
					return {
						'warning': {
							'title': 'Alerta',
							'message': _("""El RIF ingresado no pertenece a ningún contacto.""")
						}
					}
		else:
			self._clean_ticket()
			self.search_contact = False
			self.is_partner_search = False
			return {
				'domain':{
					'search_contact':[]
				},
			}

	###############################################################################################
	#AFFILIATED CONTACT SEARCH
	###############################################################################################
	@api.onchange('affiliated_partner_id')
	def _search_by_affiliated_partner(self):
		"""Busca cliente por nombre"""
		if self.affiliated_partner_id:
			self.affiliated_affiliated_number = self.affiliated_partner_id.affiliated
			self.affiliated_vat = self.affiliated_partner_id.vat
		else:
			self.affiliated_affiliated_number = False
			self.affiliated_vat = False
	
	@api.onchange('affiliated_affiliated_number')
	def _search_by_affiliated_number(self):
		"""Busca cliente por afiliado"""
		if self.affiliated_affiliated_number:
			partner_id = self.env['res.partner'].search([('affiliated','=',self.affiliated_affiliated_number), ('contact_type','in', ['0','1'])], limit=1)
			if partner_id:
				self.affiliated_partner_id = partner_id
			else:
				raise ValidationError(_("""El número de afiliado no pertenece a ningun contacto."""))

	@api.onchange('affiliated_vat')
	def _search_by_affiliated_vat(self):
		"""Busca cliente por RIF"""
		if self.affiliated_vat:
			partner_id = self.env['res.partner'].search([('vat','=',self.affiliated_vat), ('contact_type','in', ['0','1'])], limit=1)
			if partner_id:
				self.affiliated_partner_id = partner_id
			else:
				raise ValidationError(_("""El RIF ingresado no pertenece a ningun contacto."""))

	###############################################################################################
	#VALIDATIONS
	###############################################################################################
	@api.onchange('partner_id')
	def _inactive_alert(self):
		"""Alerta si el contacto esta inactivo"""
		if self.partner_id and self.partner_id.status_customer == '0':
			return {
				'warning': {
					'title': 'Alerta',
					'message': """Cliente afiliado esta INACTIVO."""
				}
			}

	@api.onchange('partner_id', 'ticket_type_id')
	def _onchange_ticket_unique(self):
		if self.partner_id and self.ticket_type_id:
			"""Alerta si existe algun ticket repetido con el mismo (cliente, requerimento)"""
			tickets = self.search([('partner_id','=',self.partner_id.id), ('ticket_type_id','=',self.ticket_type_id.id)])
			tickets = tickets.filtered(lambda s: s.stage_id.is_close == False) if tickets else False

			if tickets:
				duplicated = ''
				for t in tickets: duplicated += '%s (#%s)\n' % (t.name, t.id)

				return {
					'warning': {
						'title': 'Alerta',
						'message': 'Este Cliente ya tiene Ticket(s) asociado a esta solicitud:\n%s' % duplicated
					}
				}

	@api.constrains('partner_id', 'ticket_type_id', 'stage_id', 'product_lot')
	def _constrains_ticket_unique(self):
		"""
			Valida si existe un ticket abierto con los valores
			(Cliente, Requerimiento, Producto) para evitar repetidos
		"""
		tickets = self.search([
			('partner_id','=',self.partner_id.id),
			('ticket_type_id','=',self.ticket_type_id.id),
			('product_lot','=',self.product_lot.id),
			('id','!=',self.id)
		])
		tickets = tickets.filtered(lambda s: s.stage_id.is_close == False) if tickets else False
		
		if tickets:
			duplicates = ''
			for t in tickets: duplicates += '%s (#%s)\n' % (t.name, t.id)
			raise ValidationError(_('Este Cliente ya tiene Ticket(s) asociado a esta solicitud:\n%s' % duplicates))

	@api.constrains('cluster_id', 'ticket_type_id')
	def _constraint_excluded_cluster(self):
		if self.cluster_id and self.ticket_type_id and self.cluster_id.id in self.ticket_type_id.excluded_cluster_ids.ids:
			raise ValidationError(_('El cluster del afiliado no aplica para %s.' % self.ticket_type_id.name))
	
	@api.constrains('ticket_type_id', 'product_lot')
	def _constraint_excluded_negotiation_type(self):
		"""
			Valida si el tipo de negociacion del producto seleccionado del cliente
			Puede ser atendido por el tipo de requerimiento del ticket
		"""
		if(
			self.ticket_type_id.devices and\
			self.ticket_type_id.excluded_negotiation_type_id and\
			self.product_lot and\
			self.product_lot.negotiation_type_id in self.ticket_type_id.excluded_negotiation_type_id
		):
			raise ValidationError(_('El Modelo de negocio del equipo del cliente no aplica para este requerimiento.'))

	@api.constrains('include_failure', 'failure')
	def _constraint_include_failure(self):
		if self.include_failure and not self.failure:
			raise ValidationError(_("""Selecciona al menos una falla para continuar."""))

	@api.onchange('stage_id')
	def _close_stage_id(self):
		if self.stage_id and self.stage_id.is_close and self.substages:
			if not self.substage_id.is_close:
				raise ValidationError(_("""Debe seleccionar una etapa resolutora de cierre."""))
			elif self.causal_substage_ids:
				if self.causal_id:
					raise UserError("Debe confirmar un causal para continuar")
				else:
					raise UserError("Debe seleccionar un causal para continuar")

	###############################################################################################
	#SUB-STAGES AND CLOSE TICKET
	###############################################################################################
	@api.onchange('stage_id')
	def _determine_substage(self):
		"""Determina la etapa inicial para las etapas resolutoras del requerimiento"""
		if self.stage_id and self.ticket_type_id.stage_id and self.stage_id.id == self.ticket_type_id.stage_id.id:
			if not self.substage_id and self.substages:
				self.substage_id = self.substages.ids[0]
			self.show_substages = True
		else:
			self.show_substages = False

	def _close_ticket(self):
		"""
			Se asigna al ticket el area resolutora principal (Area resolutora del requerimiento)
			e inmediatamente se va al estado de cierre principal mas cercando (por secuencia)
			del area resolutora principal
		"""
		self = self.sudo()
		self.team_id = self.ticket_type_id.team_id
		self.stage_id = self.team_id.stage_ids.filtered(lambda stage: stage.is_close and not stage.is_sub_stage)[0]
		user_id , user_domain = self._determine_user_to_assign(self.ticket_type_id.select_user_id, self.ticket_type_id.user_ids)
		self._determine_substage()
		self.user_domain = user_domain
		self.user_id = user_id
		self.date_reached = datetime.now()

	def close_ticket_button(self):
		if self.causal_id: self._close_ticket()
		else: raise ValidationError(_("""Selecciona un causal para continuar."""))

	@api.onchange('substage_id')
	def _onchange_substage_id(self):
		"""
			Al seleccionar una etapa resolutora de cierre, automaticamente se pasa
			a la etapa de cierre mas cercana del equipo de mesa asignado al ticket
			sino se cambia al area resolutora de la subetapa seleccionada
		"""
		if self.substage_id:
			if self.substage_id.is_close:
				if not self.causal_substage_ids: self._close_ticket()
				else:
					self.there_is_causal = True
					return {
						'warning': {
							'title': 'Alerta',
							'message': """Antes de finalizar, edite el ticket y asigne un causal para continuar."""
						}
					}
			else:
				if self.substage_id.team_id:
					self.team_id = self.substage_id.team_id
				if self.substage_id.select_user_id:
					self.user_id , self.user_domain = self._determine_user_to_assign(self.substage_id.select_user_id, self.substage_id.user_ids)

	###############################################################################################
	# MAILS
	###############################################################################################
	def _track_template(self, changes):
		"""
			Permite enviar una plantilla de correo electronico personalizada
			seleccionandola desde el requerimiento, esta unicamente sera enviada en
			etapas de cierre.
		"""
		res = super(HelpdeskTicket, self)._track_template(changes)
		ticket = self[0]
		if 'stage_id' in changes and ticket.stage_id.is_close and ticket.ticket_type_id.template_id:
			res['stage_id'] = (
				ticket.ticket_type_id.template_id,
				{
					'auto_delete_message': True,
					'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
					'email_layout_xmlid': 'mail.mail_notification_light'
				}
			)
		elif 'stage_id' in changes and ticket.stage_id.template_id:
			res['stage_id'] = (
				ticket.stage_id.template_id,
				{
					'auto_delete_message': True,
					'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
					'email_layout_xmlid': 'mail.mail_notification_light'
				}
			)
		return res

	###############################################################################################
	# SLA politics
	###############################################################################################
	@api.onchange('substage_id', 'sla_deadline')
	def _onchange_substage_time(self):
		if self.substage_id and self.sla_deadline and self.substage_id.time_percent and self.sla_ids:
			deadline = self.substage_time or self.create_date
			working_calendar = self.team_id.resource_calendar_id or self.env.company.resource_calendar_id

			if not working_calendar:
				self.deadline = deadline
				return

			total_minutes = (self.sla_ids[0].time_days * working_calendar.hours_per_day + self.sla_ids[0].time_hours) * 60
			minutes = int(total_minutes * self.substage_id.time_percent / 100)
			
			days = (minutes / 60) // working_calendar.hours_per_day
			minutes -= days * 60 * working_calendar.hours_per_day

			hours = minutes // 60
			
			minutes -= hours * 60

			if days > 0:
				deadline = working_calendar.plan_days(days + 1, deadline, compute_leaves=True)
				create_dt = self.substage_time or self.create_date
				deadline = deadline.replace(hour=create_dt.hour, minute=create_dt.minute, second=create_dt.second, microsecond=create_dt.microsecond)

				deadline_for_working_cal = working_calendar.plan_hours(0, deadline)
				if deadline_for_working_cal and deadline.day < deadline_for_working_cal.day:
					deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
			
			deadline = working_calendar.plan_hours(hours, deadline, compute_leaves=True)
			self.substage_time = working_calendar.plan_minutes(minutes, deadline, compute_leaves=True)
	
	def _sla_find(self):
		""" Find the SLA to apply on the current tickets
			:returns a map with the tickets linked to the SLA to apply on them
			:rtype : dict {<helpdesk.ticket>: <helpdesk.sla>}
		"""
		tickets_map = {}
		sla_domain_map = {}

		def _generate_key(ticket):
			""" Return a tuple identifying the combinaison of field determining the SLA to apply on the ticket """
			fields_list = self._sla_reset_trigger()
			key = list()
			for field_name in fields_list:
				if ticket._fields[field_name].type == 'many2one':
					key.append(ticket[field_name].id)
				else:
					key.append(ticket[field_name])
			return tuple(key)

		"""Eliminamos del dominio la busqueda de politicas por prioridad del ticket"""
		for ticket in self:
			if ticket.team_id.use_sla:  # limit to the team using SLA
				key = _generate_key(ticket)
				# group the ticket per key
				tickets_map.setdefault(key, self.env['helpdesk.ticket'])
				tickets_map[key] |= ticket
				# group the SLA to apply, by key
				if key not in sla_domain_map:
					sla_domain_map[key] = [('stage_id.sequence', '>=', ticket.stage_id.sequence), '|', ('ticket_type_id', '=', ticket.ticket_type_id.id), ('ticket_type_id', '=', False)]

		"""Filtramos unicamente las politicas que contengan el cluster asignado al cliente"""
		result = {}
		for key, tickets in tickets_map.items():  # only one search per ticket group
			domain = sla_domain_map[key]
			result[tickets] = self.env['helpdesk.sla'].search(domain).filtered(lambda r: self.cluster_id in r.cluster_ids)  # SLA to apply on ticket subset

		return result

	@api.model
	def _sla_reset_trigger(self):
		""" Get the list of field for which we have to reset the SLAs (regenerate) """
		"""Eliminamos el campo 'priority' como trigger para la busqueda de politicas"""
		return ['ticket_type_id', 'cluster_id']

	###############################################################################################
	# import data
	###############################################################################################

	@api.constrains('team_id')
	def _onchange_team_id_import_date(self):
		if self._context.get('import_file', False):
			self._onchange_team_id()
	
	@api.constrains('ticket_type_id')
	def _set_team_id_import_date(self):
		if self._context.get('import_file', False):
			self._set_team_id()
			if self.ticket_type_id: 
				if self.ticket_type_id.include_affiliated:
					if self.affiliated_partner_id:
						self._search_by_affiliated_partner()
					elif self.affiliated_affiliated_number:
						self._search_by_affiliated_number()
						self.affiliated_vat = self.affiliated_partner_id.vat
					elif self.affiliated_vat:
						self._search_by_affiliated_vat()
						self.affiliated_affiliated_number = self.affiliated_partner_id.affiliated
					else:
						raise ValidationError("Debe especificar un cliente a incorporar con este requerimiento")
			if self.ticket_type_id.devices and not self.product_lot:
				raise ValidationError("Debe especificar un equipo con este requerimiento")
			
			self.message_post(body='Ticket de Mesa de Ayuda creado', subtype='helpdesk.mt_ticket_new')

	def send_user_email(self, env):
		if self._context.get('import_file', False) and not self._context.get('test_import', False):
			for rec in self:
				lang = rec.user_id.partner_id.lang if rec.user_id.partner_id else None
				rec.with_context(lang=lang)._message_auto_subscribe_notify([rec.user_id.partner_id.id], 'mail.message_user_assigned')

				mail = self.env['mail.mail'].search([('res_id', '=', rec.id), ('state', '=', 'outgoing')], limit=1)
				if mail:
					mail.send()

	@api.constrains('partner_id', 'affiliated', 'vat', 'partner_email')
	def _constrains_import_data(self):
		if self._context.get('import_file', False):
			if self.affiliated:
				if self.partner_id and self.affiliated != self.partner_id.affiliated:
					res = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
					parents = [res.parent_id]
					for parent in parents:
						if parent.parent_id:
							parents.append(parent.parent_id)
					if self.partner_id in parents:
						self.partner_id = res
					else:
						raise ValidationError('El numero de afiliación no concuerda con el cliente especificado')
				elif not self.partner_id:
					self.partner_id = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
					
				self._product_import_data()

				if self.vat and self.vat != self.partner_id.vat:
					raise ValidationError('El RIF no concuerda con el cliente especificado')
				
				if self.partner_email and self.partner_email != self.partner_id.email:
					raise ValidationError('El correo especificado no concuerda con el cliente (Este campo puede ser eliminado de la plantilla ya que es cargado automáticamente).')
				self.cluster_id = self.partner_id.cluster_id
			else:
				raise ValidationError("Debe ingresar el numero de afiliación del cliente para identificarlo inequívocamente")

	def _product_import_data(self):
		if self.product_lot and self.product_lot.partner_id != self.partner_id:
			raise ValidationError("El numero de serial no pertenece a un equipo del cliente especificado.")

	############################################################################################
	# stage and substage flow
	############################################################################################

	@api.depends('date_reached')
	def _set_total_time(self):
		for rec in self:
			if rec.date_reached:
				working_calendar = rec.team_id.resource_calendar_id or rec.env.company.resource_calendar_id
				rec.total_time = working_calendar.get_work_hours_count(rec.create_date, rec.date_reached)
			else:
				rec.total_time = False

	def create(self, vals):
		res = super(HelpdeskTicket, self).create(vals)
		for rec in res:
			rec.create_history_lines()
			if rec.sla_status_ids:
				rec.sudo().final_sla_status = rec.sla_status_ids[0].status
		return res

	def create_history_lines(self):
		pretime = False
		for substage in self.ticket_type_id.substage_ids:
			time = self.calculate_substage_time(substage, pretime)
			self.env['helpdesk.stage.history'].sudo().create({
					"substage_id": substage.id,
					"team_id": substage.team_id.id,
					"ticket_id": self.id,
					"substage_time": pretime if not time and not substage.is_close else time,
				})
			pretime = pretime if not time and not substage.is_close else time
			time = False
		if self.stage_history:
			self.stage_history[0].date_assigned = self.create_date
		else:
			self.date_reached = self.create_date

	def calculate_substage_time(self, substage, pretime):
		if substage and self.sla_deadline and substage.time_percent and self.sla_status_ids:
			deadline = pretime or self.create_date
			working_calendar = self.team_id.resource_calendar_id or self.env.company.resource_calendar_id

			if not working_calendar:
				self.deadline = deadline
				return

			total_minutes = (self.sla_status_ids[0].sla_id.time_days * working_calendar.hours_per_day + self.sla_status_ids[0].sla_id.time_hours) * 60
			minutes = int(total_minutes * substage.time_percent / 100)
			
			days = (minutes / 60) // working_calendar.hours_per_day
			minutes -= days * 60 * working_calendar.hours_per_day

			hours = minutes // 60
			
			minutes -= hours * 60

			if days > 0:
				deadline = working_calendar.plan_days(days + 1, deadline, compute_leaves=True)
				create_dt = pretime or self.create_date
				deadline = deadline.replace(hour=create_dt.hour, minute=create_dt.minute, second=create_dt.second, microsecond=create_dt.microsecond)

				deadline_for_working_cal = working_calendar.plan_hours(0, deadline)
				if deadline_for_working_cal and deadline.day < deadline_for_working_cal.day:
					deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
			
			deadline = working_calendar.plan_hours(hours, deadline, compute_leaves=True)
			return working_calendar.plan_minutes(minutes, deadline, compute_leaves=True)

	def write(self, vals):
		stage_old = self.stage_id
		substage_old = self.substage_id

		res = super(HelpdeskTicket, self).write(vals)

		# dont validate when import
		if not self._context.get('import_file', False):
			if not self.env.user.has_group("helpdesk_ticket.group_helpdesk_stage"):
				if self.stage_id.sequence < stage_old.sequence:
					raise ValidationError("No tiene permiso para retroceder entre las etapas.")
				if self.substage_id.sequence < substage_old.sequence:
					raise ValidationError("No tiene permiso para retroceder entre las etapas resolutoras.")

			if self.stage_history:
				self = self.sudo()
				working_calendar = self.team_id.resource_calendar_id or self.env.company.resource_calendar_id
				lines = self.stage_history.filtered(lambda s: not s.history_line_close)
				if self.substage_id.sequence > substage_old.sequence:
					for line in lines:
						if line.substage_id == substage_old:
							line.date_reached = datetime.now()
							line.execution_time = working_calendar.get_work_hours_count(line.date_assigned, line.date_reached)
							line.history_line_close = True
							if line.date_assigned and not line.date_reached:
								if line.date_assigned > line.substage_time:
									line.sla_status = 'failed'
							elif line.date_reached:
								if line.date_reached <= line.substage_time:
									line.sla_status = 'reached'
								elif line.date_reached > line.substage_time:
									line.sla_status = 'failed'
							continue
						elif line.substage_id == self.substage_id:
							if not line.substage_id.is_close:
								line.date_assigned = datetime.now()
								if line.date_assigned <= line.substage_time:
									line.sla_status = 'in_progress'
								else:
									line.sla_status = 'failed'
								break
						else:
							line.history_line_close = True

				if self.env.context.get('no_create_lines', False) and not self.go_back:
					self.go_back = True

				if self.stage_id.sequence > stage_old.sequence:
					lines = lines.filtered(lambda s: not s.history_line_close)
					if self.stage_id.is_close:
						for line in lines:
							if line.date_assigned:
								line.date_reached = datetime.now()
								line.execution_time = working_calendar.get_work_hours_count(line.date_assigned, line.date_reached)
							if line.substage_id == self.substage_id:
								line.date_reached = datetime.now()
							line.history_line_close = True
						self.final_sla_status = self.sla_status_ids[0].status
					elif self.substage_id == lines[0].substage_id and not lines[0].history_line_close:
						if not lines[0].date_assigned:
							lines[0].date_assigned = self.create_date if not self.go_back else datetime.now()
						if lines[0].date_assigned <= lines[0].substage_time:
							lines[0].sla_status = 'in_progress'
						else:
							lines[0].sla_status = 'failed'
					
				if (self.stage_id.sequence < stage_old.sequence or self.substage_id.sequence < substage_old.sequence) and not self.env.context.get('no_create_lines', False):
					self.causal_id = False
					self.there_is_causal = False
					for line in lines:
						if line.date_assigned:
							line.date_reached = datetime.now()
							line.execution_time = working_calendar.get_work_hours_count(line.date_assigned, line.date_reached)
							if line.date_reached <= line.substage_time:
								line.sla_status = 'reached'
							elif line.date_reached > line.substage_time:
								line.sla_status = 'failed'
						line.history_line_close = True
					
					
					self.env['helpdesk.stage.history'].sudo().create({
						"substage_id": False,
						"team_id": False,
						"ticket_id": self.id,
						"substage_time": False,
						"history_line_close": True,
					})
					self.create_history_lines()

					lines = self.stage_history.filtered(lambda s: not s.history_line_close)
					if self.stage_id.sequence < stage_old.sequence:
						self.with_context(no_create_lines=True).write({'substage_id': self.substages[0]})
						if stage_old.is_close:
							lines[0].date_assigned = datetime.now()
							if lines[0].date_assigned <= lines[0].substage_time:
								lines[0].sla_status = 'in_progress'
							else:
								lines[0].sla_status = 'failed'
					else:
						for line in lines:
							if self.substage_id == line.substage_id and not line.substage_id.is_close:
								line.date_assigned = datetime.now()
								if line.date_assigned <= line.substage_time:
									line.sla_status = 'in_progress'
								else:
									line.sla_status = 'failed'
								break
							line.history_line_close = True
		return res

	@api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
	def _compute_sla_deadline(self):
		""" Keep the deadline for the last stage (closed one), so a closed ticket can have a status failed.
			Note: a ticket in a closed stage will probably have no deadline
		"""
		for ticket in self:
			status_not_reached = ticket.sla_status_ids.filtered(lambda status: not status.reached_datetime)
			ticket.sla_deadline = min(status_not_reached.mapped('deadline')) if status_not_reached else ticket.sla_deadline


class HelpdeskSLAStatus(models.Model):
	_inherit = 'helpdesk.sla.status'

	@api.constrains('ticket_id', 'sla_id')
	def _update_ticket_priority(self):
		"""Asigna la prioridad de la politica al ticket en cuestion"""
		if self.ticket_id and self.sla_id:
			self.ticket_id.priority = self.sla_id.priority

	@api.depends('deadline', 'reached_datetime')
	def _compute_status(self):
		""" Note: this computed field depending on 'now()' is stored, but refreshed by a cron """
		for status in self:
			# if reached_datetime, SLA is finished: either failed or succeeded
			if status.reached_datetime and status.deadline:
				status.status = 'reached' if status.reached_datetime < status.deadline else 'failed'
			# reached a SLA without deadline: ongoing as it is not won if no deadline
			elif status.reached_datetime:
				status.status = 'ongoing'
			# if not finished, deadline should be compared to now()
			else:
				status.status = 'ongoing' if (not status.deadline or status.deadline > fields.Datetime.now()) else 'failed'
			status.sudo().ticket_id.final_sla_status = status.status

############################################################################################
# Override create definition
############################################################################################

def create(self, list_value):
	now = fields.Datetime.now()
	teams = self.env['helpdesk.team'].browse([vals['team_id'] for vals in list_value if vals.get('team_id')])
	team_default_map = dict.fromkeys(teams.ids, dict())
	
	for team in teams:
		team_default_map[team.id] = {
			'stage_id': team._determine_stage()[team.id].id,
			'user_id': team._determine_user_to_assign()[team.id].id
		}

	for vals in list_value:
		partner_id = vals.get('partner_id', False)
		partner_name = vals.get('partner_name', False)
		partner_email = vals.get('partner_email', False)
		if partner_name and partner_email and not partner_id:
			try:
				vals['partner_id'] = self.env['res.partner'].find_or_create(
					tools.formataddr((partner_name, partner_email))
				)
			except UnicodeEncodeError:
				vals['partner_id'] = self.env['res.partner'].create({
					'name': partner_name,
					'email': partner_email,
				}).id

	partners = self.env['res.partner'].browse([vals['partner_id'] for vals in list_value if 'partner_id' in vals and vals.get('partner_id') and 'partner_email' not in vals])
	partner_email_map = {partner.id: partner.email for partner in partners}
	partner_name_map = {partner.id: partner.name for partner in partners}

	for vals in list_value:
		if vals.get('team_id'):
			team_default = team_default_map[vals['team_id']]
			if 'stage_id' not in vals:
				vals['stage_id'] = team_default['stage_id']
			if 'user_id' not in vals:
				vals['user_id'] = team_default['user_id']
			if vals.get('user_id'):
				vals['assign_date'] = fields.Datetime.now()
				vals['assign_hours'] = 0

		if vals.get('partner_id') in partner_email_map:
			vals['partner_email'] = partner_email_map.get(vals['partner_id'])
		if vals.get('partner_id') in partner_name_map:
			vals['partner_name'] = partner_name_map.get(vals['partner_id'])
		if vals.get('stage_id'):
			vals['date_last_stage_update'] = now

	tickets = super(HDT, self).create(list_value)
	# make customer and portfolio_user followers
	for ticket in tickets:
		####################################################################################
		# Here we call message_subscribe with sudo permission to bypass
		# check_access_rule('write') of that function and allow create tickets
		# Aditional we add portfolio user as follower
		####################################################################################
		partners=[]
		if ticket.regional_manager:
			partners += ticket.regional_manager.partner_id.ids
		if ticket.portfolio_user.partner_id:
			partners += ticket.portfolio_user.partner_id.ids
			
		if partners:
			ticket.sudo().message_subscribe(partner_ids=partners)
		
		ticket._portal_ensure_token()

	tickets.sudo()._sla_apply()

	if self._context.get('import_file', False) and not self._context.get('test_import', False):
		create_values_list = {}
		for thread, values in zip(tickets, list_value):
			create_values = dict(values)
			for key, val in self._context.items():
				if key.startswith('default_') and key[8:] not in create_values:
					create_values[key[8:]] = val
			thread._message_auto_subscribe(create_values, followers_existing_policy='update')
			create_values_list[thread.id] = create_values
		
		if not self._context.get('mail_notrack'):
			track_threads = tickets.with_lang()
			tracked_fields = self._get_tracked_fields()
			for thread in track_threads:
				create_values = create_values_list[thread.id]
				changes = [field for field in tracked_fields if create_values.get(field)]
				changes.append('stage_id')
				# based on tracked field to stay consistent with write
				# we don't consider that a falsy field is a change, to stay consistent with previous implementation,
				# but we may want to change that behaviour later.
				thread._message_track_post_template(changes)
		
	# 	for rec in tickets:
	# 		lang = rec.user_id.partner_id.lang if rec.user_id.partner_id else None
	# 		rec.with_context(lang=lang)._message_auto_subscribe_notify([rec.user_id.partner_id.id], 'mail.message_user_assigned')

	# 		mail = self.env['mail.mail'].search([('res_id', '=', rec.id), ('state', '=', 'outgoing')], limit=1)
	# 		if mail:
	# 			mail.send()

	return tickets

HDT.create = create # assign the re-definition of create

###############################################################################################
# import data
###############################################################################################

@api.model
def default_get(self, fields):
	result = super(HDT, self).default_get(fields)
	if result.get('team_id') and fields:
		team = self.env['helpdesk.team'].browse(result['team_id'])
		if 'user_id' in fields and 'user_id' not in result:  # if no user given, deduce it from the team
			result['user_id'] = team._determine_user_to_assign()[team.id].id
		if 'stage_id' in fields and 'stage_id' not in result and not self._context.get('import_file', False):  # if no stage given, deduce it from the team
			result['stage_id'] = team._determine_stage()[team.id].id
	return result

HDT.default_get = default_get