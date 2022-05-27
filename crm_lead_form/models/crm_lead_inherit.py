# -*- coding: utf-8 -*-

from datetime import datetime, date
from itertools import product
from logging import currentframe, raiseExceptions
from odoo.tools.translate import _
from odoo import models, fields, api, exceptions


class Lead(models.Model):
	_inherit = 'crm.lead'
	_description = 'herencia de planilla de oportunidades'

	stage_code = fields.Integer(related="stage_id.stage_code")
	current_stage = fields.Integer(default= 1)
	type_negotiation_id = fields.Many2one(comodel_name='crm.negotiation', string="Tipo de negociación", ondelete="restrict")
	type_point_sale_id = fields.Many2one(comodel_name='crm.point.sale', string="Tipo de comunicación", ondelete="restrict")
	type_code = fields.Integer(related="type_point_sale_id.type_code")
	company_pos_id = fields.Many2one(comodel_name='crm.company.pos', string="Operadora Telefónica", ondelete="restrict")
	bank_segment_id = fields.Many2one(comodel_name='bank.segment', string="Banca o segmento que refiere", readonly=True, ondelete="restrict")
	mgr_regional_id = fields.Many2one(comodel_name='mgr.regional', string="Gerencia regional bancas", readonly=True, ondelete="restrict")
	event_name_id = fields.Many2one(comodel_name='event.name', string="Nombre del evento", ondelete="restrict")
	kind_attention = fields.Selection([('1', 'Tradicional'), ('2', 'Evento'), ('3', 'VIP')], string="Tipo de atención")
	origin_id = fields.Many2one(comodel_name='crm.origin', string="Origen", ondelete="restrict")
	affiliated = fields.Char(string="Número de afiliación")
	task = fields.Char(string="Tarea")
	stage_id = fields.Many2one(tracking=False, ondelete="restrict")

	progress_colour = fields.Selection([
		('success', 'Green'),
		('normal', 'Grey'),
		('cancelled', 'Red')
	], string='Calour State', copy=False, default='normal')
	product_quantity = fields.Integer(string="Cantidad de Producto Estimada")

	related_company = fields.Many2one('res.partner',string="Empresa relacionada", readonly=True)
	denomination = fields.Char(string="Denominación comercial", readonly=True, force_save=True)
	vat = fields.Char(string="RIF", readonly=True)
	company_address=fields.Many2one('res.partner', string="Dirección de factura")
	region = fields.Many2one('crm.region', string='Región', readonly=True, ondelete="restrict")
	phone_two = fields.Char(string="Teléfono 2", readonly=True)
	phone_three = fields.Char(string="Teléfono 3", readonly=True)
	acquire_bank_id = fields.Many2one('acquiring.bank', string="Banco Adquiriente", readonly=True, ondelete="restrict")
	cluster_id = fields.Many2one('segmentation.cluster', string='Cluster', readonly=True, ondelete="restrict")
	name_owner = fields.Char(string="Nombre y Apellido del Propietario", readonly=True)

	date_deadline_condition = fields.Boolean(copy=False)
	mail_partner_id = fields.Many2one('res.partner')
	address_affiliated = fields.Char()

	# checks, fechas asociadas y fecha de cita
	###########################################################################################################
	failed_contact_1 = fields.Boolean(string="Primer contacto fallido", copy=False)
	failed_contact_2 = fields.Boolean(string="Segundo contacto fallido", copy=False)
	failed_contact_3 = fields.Boolean(string="Tercer contacto fallido", copy=False)
	budget_send = fields.Boolean(string="Presupuesto enviado", copy=False)
	budget_confirmed = fields.Boolean(string="Presupuesto confirmado", copy=False)
	scheduled_date = fields.Boolean(string="Asistencia a cita confirmada", copy=False)
	successful_contact = fields.Boolean(string="Contacto exitoso", copy=False)
	fail_button = fields.Boolean(invisible=True)
	
	failed_contact_1_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	failed_contact_2_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	failed_contact_3_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	budget_send_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	budget_confirmed_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	scheduled_date_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	successful_contact_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	
	date_deadline = fields.Date(copy=False)
	appointment_date = fields.Date(string="Fecha de cita", copy=False)
	###########################################################################################################

	# fechas de seguimiento de etapas
	###########################################################################################################
	# pendiente de gestion
	stage_1_start = fields.Datetime(string="Fecha de inicio", copy=False)
	stage_1_end = fields.Datetime(string="Fecha de finalización", copy=False)

	# contacto fallido
	stage_2_start = fields.Datetime(string="Fecha de inicio", copy=False)
	stage_2_end = fields.Datetime(string="Fecha de finalización", copy=False)
	
	# en negociacion
	stage_3_start = fields.Datetime(string="Fecha de inicio", copy=False)
	stage_3_end = fields.Datetime(string="Fecha de finalización", copy=False)
	
	# en evaluacion del cliente
	stage_4_start = fields.Datetime(string="Fecha de inicio", copy=False)
	stage_4_end = fields.Datetime(string="Fecha de finalización", copy=False)
	
	# en espera de cita
	stage_5_start = fields.Datetime(string="Fecha de inicio", copy=False)
	stage_5_end = fields.Datetime(string="Fecha de finalización", copy=False)
	
	@api.constrains('stage_1_start')
	def set_inicial_date(self):
		if not self.stage_1_start:
			self.stage_1_start = datetime.now()

	# # negociacion exitosa
	# stage_6_start = fields.Datetime(string="Fecha de inicio")
	# stage_6_end = fields.Datetime(string="Fecha de finalización")
	
	# # negociacion fallida
	# stage_7_start = fields.Datetime(string="Fecha de inicio")
	# stage_7_end = fields.Datetime(string="Fecha de finalización")

	@api.onchange('company_address')
	def _onchange_company_address(self):
		if self.company_address and self.company_address.affiliated:
			self.address_affiliated = self.company_address.affiliated
		else:
			self.address_affiliated = False

	@api.onchange('address_affiliated')
	def _onchange_address_affiliated(self):
		if self.address_affiliated:
			address = self.env['res.partner'].search([('affiliated', '=', self.address_affiliated)], limit=1)
			if address:
				self.company_address = address
			else:
				raise exceptions.ValidationError("El numero de afiliación no concuerda con ningún cliente")

	###########################################################################################################
	
	def write(self,vals):
		old_stage = self.stage_id
		res = super(Lead, self).write(vals)
		if vals.get('stage_id', False) and self.stage_id != old_stage:
			if self.stage_id.stage_code == 6:
				message = """Oportunidad ganada <ul><li>""" 
			else:
				message = """Etapa cambiada <ul><li>"""

			message += """Etapa: """ + old_stage.name + """ <span>&#8594;<span/> """ + self.stage_id.name + """<ul/>"""
			self.message_post(body=message, subtype='mt_lead_stage')
		return res

	regional_manager = fields.Many2one(comodel_name='res.users', string="Gerente Regional", readonly=True)
	product_type = fields.Selection([
		('1', 'POS'),
		('2', 'Accesorios'),
		('3', 'POS y Accesorios')
	], string="Tipo de Producto")

	# cierre previsto no debe ser editable despues de la creacion
	@api.constrains('date_deadline')
	def date_deadline_constrain(self):
		if self.date_deadline and not self.date_deadline_condition:
			self.date_deadline_condition = True

	#condicion para hacer que los campos ingresados por el usuario se vuelvan solo lectura cuando un pedido de venta este confirmado
	###########################################################################################################
	def _compute_readonly_condition(self):
		cont = 0
		for rec in self.order_ids:
			if rec.state == 'sale':
				cont += 1
		if cont > 0:
			self.readonly_condition = True
		else:
			self.readonly_condition = False
	readonly_condition = fields.Boolean(compute = _compute_readonly_condition)
	###########################################################################################################

	#condicion para no crear una oportunidad con un contacto inactivo 
	###########################################################################################################
	@api.onchange('partner_id')
	def domain_onchange(self):
		if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1' or not self.partner_id:
			self.mgr_regional_id = self.partner_id.mgr_regional_id
			self.bank_segment_id = self.partner_id.bank_segment_id
			self.user_id = self.partner_id.user_id
			self.team_id = self.partner_id.team_id
			self.regional_manager = self.partner_id.regional_manager

			self.affiliated = self.partner_id.affiliated
			self.email_from = self.partner_id.email
			self.related_company = self.partner_id.parent_id
			self.phone = self.partner_id.phone_one
			self.phone_two = self.partner_id.phone_two
			self.phone_three = self.partner_id.phone_three
			self.acquire_bank_id = self.partner_id.acquire_bank_id
			self.cluster_id = self.partner_id.cluster_id
			self.name_owner = self.partner_id.name_owner
			self.denomination = self.partner_id.denomination
			self.vat = self.partner_id.vat
			self.street = self.partner_id.street
			self.street2 = self.partner_id.street2
			self.city = self.partner_id.city
			self.state_id = self.partner_id.state_id
			self.zip = self.partner_id.zip
			self.country_id = self.partner_id.country_id
			self.region = self.partner_id.region_id
			self.company_address = self.partner_id

		else:
			raise exceptions.ValidationError('El cliente seleccionado esta INACTIVO')

	# validaciones necesarias para la carga de oportunidades por carga masiva
	@api.constrains('affiliated')
	def masive_load(self):
		if self._context.get('import_file', False):
			partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
			if partner:
					self.partner_id = partner.id
			else:
				raise exceptions.ValidationError('La afiliación ingresada no pertenece a ningun contacto')

			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1' or not self.partner_id:
				if self.date_deadline:
					if not self.mgr_regional_id:
						self.mgr_regional_id = self.partner_id.mgr_regional_id
					if not self.bank_segment_id:
						self.bank_segment_id = self.partner_id.bank_segment_id
					if self.user_id != self.partner_id.user_id:
						self.user_id = self.partner_id.user_id
						if self.user_id.partner_id.id not in self.message_partner_ids.ids:
							reg = {
							'res_id': self.id,
							'res_model': 'crm.lead',
							'partner_id': self.user_id.partner_id.id
							}
							self.env['mail.followers'].create(reg)
					if not self.team_id:
						self.team_id = self.partner_id.team_id
					if not self.regional_manager:
						self.regional_manager = self.partner_id.regional_manager
					if not self.email_from:
						self.email_from = self.partner_id.email
					if not self.related_company:
						self.related_company = self.partner_id.parent_id
					if not self.phone:
						self.phone = self.partner_id.phone_one
					if not  self.phone_two:
						self.phone_two = self.partner_id.phone_two
					if not self.phone_three:
						self.phone_three = self.partner_id.phone_three
					if not self.acquire_bank_id:
						self.acquire_bank_id = self.partner_id.acquire_bank_id
					if not self.cluster_id:
						self.cluster_id = self.partner_id.cluster_id
					if not self.name_owner:
						self.name_owner = self.partner_id.name_owner
					if not self.denomination:
						self.denomination = self.partner_id.denomination
					if not self.vat:
						self.vat = self.partner_id.vat
					if not self.street:
						self.street = self.partner_id.street
					if not self.street2:
						self.street2 = self.partner_id.street2
					if not self.city:
						self.city = self.partner_id.city
					if not self.state_id:
						self.state_id = self.partner_id.state_id
					if not self.zip:
						self.zip = self.partner_id.zip
					if not self.country_id:
						self.country_id = self.partner_id.country_id
					if not self.region:
						self.region = self.partner_id.region_id
					if self.company_address:
						self.address_affiliated = self.company_address.affiliated
					elif self.address_affiliated:
						self.company_address = self.env['res_partner'].search([('affiliated', '=', self.address_affiliated)], limit=1)
					else:
						self.company_address = self.partner_id
						self.address_affiliated = self.partner_id.affiliated
				else:
					raise exceptions.ValidationError('El campo cierre previsto es obligarorio para crear la oportunidad')
			else:
				raise exceptions.ValidationError('El cliente seleccionado esta INACTIVO')

			if self.stage_code == 1 and not self.stage_1_start:
				self.stage_1_start = datetime.now()
			if self.stage_code == 2 and not self.stage_2_start:
				self.stage_2_start = datetime.now()
			if self.stage_code == 3 and not self.stage_3_start:
				self.stage_3_start = datetime.now()
			if self.stage_code == 4 and not self.stage_4_start:
				self.stage_4_start = datetime.now()
			if self.stage_code == 5 and not self.stage_5_start:
				self.stage_5_start = datetime.now()

			count = 0
			for rec in self.env["crm.lead"].search([('affiliated', '=', self.partner_id.affiliated), ('type', '=', 'opportunity')]):
				if rec.stage_code != 6:
					count += 1
			if count > 1:
				raise exceptions.ValidationError('Ya existe una oportunidad en curso para este cliente')

	###########################################################################################################

	@api.constrains('company_address')
	def constrains_company_address(self):
		for order in self.order_ids:
			if self.company_address != order.partner_invoice_id:
				order.partner_invoice_id = self.company_address

	#condicion para no poder seleccionar un contacto inactivo
	###########################################################################################################
	@api.onchange('affiliated')
	def _onchange_affiliated(self):
		if self.affiliated:
			partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
			if partner:
					self.partner_id = partner.id
			else:
				raise exceptions.ValidationError('La afiliación ingresada no pertenece a ningun contacto')
	###########################################################################################################

	def contact_asignation(self, contact):
		pass

	# identificador secuencial unico para las oportunidades
	###########################################################################################################
	lead_sequence = fields.Char(string='Referencia', copy=False, default="Nuevo")

	_sql_constraints=[('sequence_uniq', 'UNIQUE(lead_sequence)', 'El numero de referencia debe ser único. La secuencia pudo ser alterada')]

	@api.model
	def create(self, vals):
		if vals.get('lead_sequence', 'Nuevo') == 'Nuevo' or vals.get('lead_sequence') == False:
			vals['lead_sequence'] = self.env['ir.sequence'].next_by_code('crm_lead_form.crm_lead')
		return super(Lead, self).create(vals)
	###########################################################################################################

	# presupuesto enviado
	###########################################################################################################
	# def budgets_send_compute(self):
	#     if self.quotation_count == 1 and self.budget_send == False:
	#         cont = 0
	#         for rec in self.order_ids:
	#             if rec.state == 'sent':
	#                 cont += 1
	#         if cont > 0:
	#             self.budget_send = True

	#     if self.budget_send == True and self.budget_send_date == False:
	#         self.budget_send_date = datetime.now()
	#     elif self.budget_send_date:
	#         self.budget_send = True

	# budget_send = fields.Boolean(string="Presupuesto enviado", compute=budgets_send_compute)
	###########################################################################################################

	# validacion de checks
	###########################################################################################################
	@api.constrains('failed_contact_1', 'failed_contact_2', 'failed_contact_3', 'successful_contact', 'budget_send', 'budget_confirmed', 'scheduled_date')
	def boolean_dates(self):
		if self.failed_contact_1 and self.failed_contact_1_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.failed_contact_1_date = datetime.now()
				self.current_stage = 2
				self.stage_1_end = datetime.now()
				self.stage_2_start = datetime.now()
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		if self.failed_contact_2 and self.failed_contact_2_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.failed_contact_2_date = datetime.now()
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
				
		if self.failed_contact_3 and self.failed_contact_3_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.failed_contact_3_date = datetime.now()
				# self.action_set_lost(lost_reason=12)
				# action = self.env.ref('crm.crm_lead_lost_action').read()[0]
				# return action
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		if self.successful_contact and self.successful_contact_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.successful_contact_date = datetime.now()
				if self.current_stage == 1:
					self.stage_1_end = datetime.now()
					self.stage_3_start = datetime.now()
				else:
					self.stage_2_end = datetime.now()
					self.stage_3_start = datetime.now()
				self.current_stage = 3
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		if self.budget_send and self.budget_send_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.budget_send_date = datetime.now()
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
			
		
		if self.budget_confirmed and self.budget_confirmed_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.budget_confirmed_date = datetime.now()
				if self.current_stage == 3:
					self.stage_3_end = datetime.now()
				else:
					self.stage_4_end = datetime.now()
				self.current_stage = 6
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
			
		
		if self.scheduled_date and self.scheduled_date_date == False:
			if self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.kind_attention != '2':
					self.scheduled_date_date = datetime.now()
				elif self.appointment_date and not ((self.appointment_date > date.today()) and self.scheduled_date):
					if self.order_ids.filtered(lambda s: s.state in ['sale']).sales_operational_worksheet:
						self.scheduled_date_date = datetime.now()
						self.current_stage = 6
					else:
						raise exceptions.ValidationError('Debe cargar la Planilla de Operativo de Venta en el Pedido de Venta')
				else:
					raise exceptions.ValidationError('No se pueden confirmar asistenacia a citas por adelantado')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		self.stage_id = self.env['crm.stage'].search([('stage_code', '=', self.current_stage)], limit=1).id

	###########################################################################################################
	
	# oportunidad activa unica por cliente
	###########################################################################################################
	def onchange_check_lead(self):
		"""
		Trigger a warning from javascript if duplicate record
		"""
		try:
			return self._onchange_check_lead()
		except exceptions.ValidationError as e:
			return
	
	@api.onchange('partner_id')
	def _onchange_check_lead(self):
		if self.partner_id:
			leads = self.env["crm.lead"].search([('affiliated', '=', self.partner_id.affiliated), ('type', '=', 'opportunity'), ('stage_code', '!=', 6)])
			if leads.filtered(lambda l: l.stage_code in [1, 2, 7] or (l.stage_code == 3 and not l.budget_send)):
				raise exceptions.ValidationError('Ya existe una oportunidad en curso para este cliente')
			if leads.filtered(lambda l: l.stage_code in [3, 4, 5]):
				return {
					'warning': {
						'title': 'Ya existe una oportunidad en curso para este cliente',
						'message': 'Verifique la informacion antes de continuar.'
					}
				}

	@api.constrains('partner_id')
	def _constrains_check_lead(self):
		if self.partner_id and not self._context.get('import_file', False):
			for rec in self.env["crm.lead"].search([('affiliated', '=', self.partner_id.affiliated), ('type', '=', 'opportunity')]):
				if (rec.stage_code in [1, 2, 7] or (rec.stage_code == 3 and not rec.budget_send)) and rec.id != self.id:
					raise exceptions.ValidationError('Ya existe una oportunidad en curso para este cliente')
	###########################################################################################################

	# fecha de cita
	###########################################################################################################
	@api.constrains('appointment_date')
	def _onchange_appointment_date(self):
		if self.appointment_date:
			if self.appointment_date < date.today():
				self.appointment_date = False
				raise exceptions.ValidationError('La fecha de la cita no puede ser anterior a la fecha actual')
			elif self.order_ids:
				sales = self.order_ids.filtered(lambda s: s.state == 'sale')
				for sale in sales:
					if not sale.appointment_date:
						sale.appointment_date = self.appointment_date
					elif sale.appointment_date != self.appointment_date:
						sale.appointment_date = self.appointment_date
				
			if self.stage_id.stage_code in [3, 4] and self.kind_attention == '2':
				self.stage_id = self.env['crm.stage'].search([('stage_code', '=', 5)], limit=1)
				if self.current_stage == 3:
					self.stage_3_end = datetime.now()
					self.stage_5_start = datetime.now()
				else:
					self.stage_4_end = datetime.now()
					self.stage_5_start = datetime.now()
				self.current_stage = 5

	###########################################################################################################

	# validacion de cambios de etapa
	###########################################################################################################
	@api.onchange('stage_id')
	def stage_validations(self):
		if self.current_stage == 1 and self.stage_id.stage_code == 1:
			pass

		# pendiente de gestion -> contacto fallido
		elif self.current_stage == 1 and self.stage_id.stage_code == 2:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.failed_contact_1:
					self.current_stage = 2
				else: 
					raise exceptions.ValidationError('Debe haber un contacto fallido')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# pendiente de gestion -> en negociacion
		elif self.current_stage == 1 and self.stage_id.stage_code == 3:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.successful_contact:
					self.current_stage = 3
				else: 
					raise exceptions.ValidationError('Debe haber un contacto exitoso')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# contacto fallido -> en negociacion 
		elif self.current_stage == 2 and self.stage_id.stage_code == 3:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.successful_contact:
					self.current_stage = 3
				else: 
					raise exceptions.ValidationError('Debe haber un contacto exitoso')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# contacto fallido -> negociacion fallida 
		elif self.current_stage == 2 and self.stage_id.stage_code == 7:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.fail_button:
					self.current_stage = 7
					self.stage_2_end = datetime.now()
				else:
					raise exceptions.ValidationError('Use el botón "MARCAR PERDIDO" para llevar la oportunidad a Negociación fallida')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# en negociacion -> en evaluacion del cliente
		elif self.current_stage == 3 and self.stage_id.stage_code == 4:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.budget_send:
					self.current_stage = 4
					self.stage_3_end = datetime.now()
					self.stage_4_start = datetime.now()
				else:
					raise exceptions.ValidationError('Debe existir al menos un (1) presupuesto enviado')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# en negociacion -> en espera de cita
		elif self.current_stage == 3 and self.stage_id.stage_code == 5:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.budget_confirmed:
					self.current_stage = 5
					self.stage_3_end = datetime.now()
					self.stage_5_start = datetime.now()
				else:
					raise exceptions.ValidationError('Debe existir un (1) presupuesto confirmado')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# en negociacion -> negociacion exitosa
		elif self.current_stage == 3 and self.stage_id.stage_code == 6:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.scheduled_date:
					self.current_stage = 6
					self.stage_3_end = datetime.now()
				else:
					raise exceptions.ValidationError('Debe existir un (1) pedido de venta')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# en negociacion -> negocicacion fallida
		elif self.current_stage == 3 and self.stage_id.stage_code == 7:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.fail_button:
					self.current_stage = 7
					self.stage_3_end = datetime.now()
				else:
					raise exceptions.ValidationError('Use el botón "MARCAR PERDIDO" para llevar la oportunidad a Negociación fallida')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# en evaluacion del cliente -> en espera de cita
		elif self.current_stage == 4 and self.stage_id.stage_code == 5:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.budget_confirmed:
					self.current_stage = 5
					self.stage_4_end = datetime.now()
					self.stage_5_start = datetime.now()
				else:
					raise exceptions.ValidationError('Debe existir un (1) presupuesto confirmado')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# en evaluacion del cliente -> negocacion fallida
		elif self.current_stage == 4 and self.stage_id.stage_code == 7:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.fail_button:
					self.current_stage = 7
					self.stage_4_end = datetime.now()
				else:
					raise exceptions.ValidationError('Use el botón "MARCAR PERDIDO" para llevar la oportunidad a Negociación fallida')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')

		# en espera de cita -> negociacion exitosa 
		elif self.current_stage == 5 and self.stage_id.stage_code == 6:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.scheduled_date:
					self.current_stage = 6
					self.stage_5_end = datetime.now()
				else:
					raise exceptions.ValidationError('Se debe confirmar la asistencia a la cita')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# en espera de cita -> negocacion fallida
		elif self.current_stage == 5 and self.stage_id.stage_code == 7:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.fail_button:
					self.current_stage = 7
					self.stage_5_end = datetime.now()
				else:
					raise exceptions.ValidationError('Use el botón "MARCAR PERDIDO" para llevar la oportunidad a Negociación fallida')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# negociacion exitosa -> negociacion fallida
		elif self.current_stage == 6 and self.stage_id.stage_code == 7:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				if self.fail_button:
					self.current_stage = 7
				else:
					raise exceptions.ValidationError('Use el botón "MARCAR PERDIDO" para llevar la oportunidad a Negociación fallida')
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# negociacion fallida -> pendiente de gestion 
		elif self.current_stage == 7 and self.stage_id.stage_code == 1:
			if self.partner_id and self.partner_id.contact_type in ('0', '1') and self.partner_id.status_customer == '1':
				self.current_stage = 1
				self.fail_button = False
				self.date_deadline_condition= False
				self.date_deadline = False
				self.failed_contact_1 = False
				self.failed_contact_1_date = False
				self.failed_contact_2 = False
				self.failed_contact_2_date = False
				self.failed_contact_3 = False
				self.failed_contact_3_date = False
				self.successful_contact = False
				self.successful_contact_date = False
				self.budget_send = False
				self.budget_send_date = False
				self.budget_confirmed = False
				self.budget_confirmed_date = False
				self.scheduled_date = False
				self.scheduled_date_date = False
				self.appointment_date = False
				self.stage_1_start = datetime.now()
				self.stage_1_end = False
				self.stage_2_start = False
				self.stage_2_end = False
				self.stage_3_start = False
				self.stage_3_end = False
				self.stage_4_start = False
				self.stage_4_end = False
				self.stage_5_start = False
				self.stage_5_end = False
				self.lost_reason = False
			else:
				raise exceptions.ValidationError('El cliente esta INACTIVO')
		
		# pendiente de gestion -> etapas - {contacto fallido, en negociacion}
		# contacto fallido -> etapas - {en negociacion, negociacion fallida}
		# en negociacion -> etapas - {en evaluacion del cliente, en espera de cita, negociacion fallida}
		# en evaluacion del cliente -> etapas - {en espera de cita, negociacion fallida}
		# en espera de cita -> etapas - {negociacion exitosa, negociacion fallida}
		# negociaicon fallida -> etapas - {pendiente de gestion}
		else:
			raise exceptions.ValidationError('Cambio de etapa invalido')
	###########################################################################################################

	# Modificacion del boton "marcar perdida"
	###########################################################################################################
	def action_set_lost(self, **additional_values):
		""" Lost semantic: probability = 0 or active = False """
		self.stage_id = self.env['crm.stage'].search([('stage_code', '=', 7)], limit=1)
		if self.current_stage == 2:
			self.stage_2_end = datetime.now()
		elif self.current_stage == 3:
			self.stage_3_end = datetime.now()
		elif self.current_stage == 4:
			self.stage_4_end = datetime.now()
		elif self.current_stage == 5:
			self.stage_5_end = datetime.now()
		self.current_stage = 7
		result = self.write({'probability': 0, 'automated_probability': 0, **additional_values})
		self._rebuild_pls_frequency_table_threshold()
		return result
	###########################################################################################################

	# modificacion del boton "marcar ganado"
	###########################################################################################################
	def action_set_won_rainbowman(self):
		origin = True
		if self.scheduled_date:
			origin = super(Lead, self).action_set_won_rainbowman()
			if self.current_stage == 2:
				self.stage_2_end = datetime.now()
			elif self.current_stage == 3:
				self.stage_3_end = datetime.now()
			elif self.current_stage == 4:
				self.stage_4_end = datetime.now()
			elif self.current_stage == 5:
				self.stage_5_end = datetime.now()
			self.current_stage = 6
		else:
			raise exceptions.ValidationError('Se debe confirmar la asistencia a la cita')
		return origin
	###########################################################################################################

	# accion de boton "nuevo presupuesto de alquiler"
	###########################################################################################################
	def action_view_rent_quotation(self):
		action = self.env.ref('sale_renting.rental_order_action').read()[0]
		action['context'] = {
			'default_is_rental_order': 1,
			'search_default_from_rental': 1,
			'search_default_draft': 1,
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_opportunity_id': self.id
		}
		action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
		action['views'] = [(self.env.ref('sale_renting.rental_order_primary_form_view').id, 'form')]
		return action
	###########################################################################################################

	# no tomar los estados de aprobacion como pedido de venta
	###########################################################################################################
	@api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
	def _compute_sale_data(self):
		for lead in self:
			total = 0.0
			quotation_cnt = 0
			sale_order_cnt = 0
			company_currency = lead.company_currency or self.env.company.currency_id
			for order in lead.order_ids:
				if order.state in ('draft', 'reg_manag', 'fin_approve', 'sent'):
					quotation_cnt += 1
				if order.state not in ('draft', 'reg_manag', 'fin_approve', 'sent', 'cancel'):
					sale_order_cnt += 1
					total += order.currency_id._convert(
						order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
			lead.sale_amount_total = total
			lead.quotation_count = quotation_cnt
			lead.sale_order_count = sale_order_cnt

	def action_view_sale_quotation(self):
		action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
		action['context'] = {
			'search_default_no_sale': 1,
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_opportunity_id': self.id
		}
		action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'reg_manag', 'fin_approve', 'sent'])]
		quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'reg_manag', 'fin_approve', 'sent'))
		if len(quotations) == 1:
			action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
			action['res_id'] = quotations.id
		return action

	def action_view_sale_order(self):
		action = self.env.ref('sale.action_orders').read()[0]
		action['context'] = {
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_opportunity_id': self.id,
		}
		action['domain'] = [('opportunity_id', '=', self.id), ('state', 'not in', ('draft', 'reg_manag', 'fin_approve', 'sent', 'cancel'))]
		orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'reg_manag', 'fin_approve', 'sent', 'cancel'))
		if len(orders) == 1:
			action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
			action['res_id'] = orders.id
		return action
	###########################################################################################################

	# Validacion antes de pasar a negociacion fallida, no debe haber pedidos de venta
	def mark_lost(self):
		if self.sale_order_count != 0:
			raise exceptions.ValidationError('Se debe cancelar el Pedido de Venta antes de pasar la Oportunidad a Negociación Fallida')
		else:
			action = self.env.ref('crm.crm_lead_lost_action').read()[0]
			return action
		
	# intervencion del boton para la validacion de campos
	def opportunity_with_validations(self):
		if not self.partner_id:
			raise exceptions.ValidationError('Se debe seleccionar o crear el contacto correspondiente al nuevo cliente')
			
		message = ''
		if not self.date_deadline:
			message += '·Cierre previsto' + ' \n'
		if not self.type_negotiation_id:
			message += '·Tipo de negociación' + ' \n'
		if not self.product_type : 
			message += '·Tipo de Producto' + ' \n'
		elif self.product_type and self.product_type in ['1', '3'] and not self.type_point_sale_id:
			message += '·Tipo de comunicació' + ' \n'
		elif self.type_point_sale_id and self.type_point_sale_id.type_code == 1 and not self.company_pos_id:
			message += '·Operadora Telefónica' + ' \n'
		if not self.origin_id:
			message += '·Origen' + ' \n'
		if not self.kind_attention:
			message += '·Tipo de atención' + ' \n'
		elif self.kind_attention and self.kind_attention == '2' and not self.event_name_id:
			message += '·Nombre del evento'
		
		if message != '':
			raise exceptions.ValidationError('Faltan los campos' + '\n' + message)
		else:
			for rec in self.env["crm.lead"].search([('affiliated', '=', self.partner_id.affiliated), ('id', '!=', self.id)]):
				if rec.stage_code in [1, 2, 7] or (rec.stage_code == 3 and not rec.budget_send):
					raise exceptions.ValidationError('Ya existe una oportunidad en curso para este cliente')
		
		return self.env.ref('crm.action_crm_lead2opportunity_partner').read()[0]

	def action_new_quotation(self):
		action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
		action['context'] = {
			'search_default_opportunity_id': self.id,
			'default_opportunity_id': self.id,
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_team_id': self.team_id.id,
			'default_campaign_id': self.campaign_id.id,
			'default_medium_id': self.medium_id.id,
			'default_origin': self.lead_sequence,
			'default_source_id': self.source_id.id,
			'default_company_id': self.company_id.id or self.env.company.id,
			'default_tag_ids': self.tag_ids.ids,
		}
		return action

	def send_user_email(self, env):
		for rec in self:
			if rec._context.get('import_file', False) and not rec._context.get('test_import', False):
				lang = self.user_id.partner_id.lang if self.user_id.partner_id else None
				self.mail_partner_id = self.user_id.partner_id
				self.with_context(lang=lang)._message_auto_subscribe_notify([self.user_id.partner_id.id], 'crm_lead_form.message_sale_assigned')

				mail = self.env['mail.mail'].search([('res_id', '=', rec.id), ('state', '=', 'outgoing')], limit=1)
				if mail:
					mail.send()

	# @api.constrains('message_ids')
	# def _delete_duplicate_chatter_message(self):
	# 	test = self.message_ids.filtered(lambda m: m.message_type == 'notification' and m.tracking_value_ids != [])
	# 	if test and test[0].tracking_value_ids[0].old_value_integer == test[1].tracking_value_ids[0].old_value_integer and test[0].tracking_value_ids[0].new_value_integer == test[1].tracking_value_ids[0].new_value_integer:
	# 		test[0].unlink()