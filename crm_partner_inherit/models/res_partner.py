#-*- coding: utf-8 -*-


from odoo import models, fields, api, exceptions
import datetime

from odoo.osv import query

class Partner(models.Model):
	_inherit = 'res.partner'
	_description = 'crm_partner_inherit'


	phone_one = fields.Char(string="Teléfono")
	phone_two = fields.Char(string="Teléfono 2")
	phone_three = fields.Char(string="Teléfono 3")
	is_customer = fields.Boolean( default=False, string="Cliente")
	is_supplier = fields.Boolean( default=False,string="Proveedor")
	affiliated = fields.Char(string="Numero de afiliación")
	region_id = fields.Many2one('crm.region',string='Región', ondelete="restrict")
	# bank_region_id = fields.Many2one('crm.region',string='Región bancaria')
	bank_region_id = fields.Many2one('crm.bank.region',string='Región bancaria', ondelete="restrict")
	territory_id = fields.Many2one('territory', string = "Territorio", ondelete="restrict")
	denomination = fields.Char(string="Denominación comercial")
	expired_rif = fields.Date(string="Vencimiento del Rif")
	contact_type = fields.Selection([
									('0', 'Cliente'),
									('1', 'Cliente/Proveedor'),
									('2', 'Proveedor'),
									('3', 'Empleado'),
									('4', 'Otro'),
									], string="El contacto es")
	
	member_ids = fields.One2many('res.users', related="team_id.member_ids")

	_sql_constraints = [
	('afiliated_uniq', 'unique (affiliated)', "El campo Afiliado debe ser unico"),
	('region_id_required', 'CHECK(name_owner IS NOT NULL)', "El campo Region no debe ser nulo"),]

	# seccion afiliacion
	date_affiliated = fields.Date(string ='Fecha de Afiliación', default=datetime.date.today())
	#create_date = fields.Date(string ='Creado en', default=datetime.date.today())
	status_customer = fields.Selection([
											('1', 'ACTIVO'),
											('0', 'INACTIVO'),
											], string="Estado afiliación", default='1')
	status_supplier = fields.Selection([
											('1', 'ACTIVO'),
											('0', 'INACTIVO'),
											], string="Estatus proveedor", default='1')

	name_owner =fields.Char(string ="Nombre y Apellido del Propietario")
	UBA_id = fields.Many2one(comodel_name ='crm.uba', string="UBA", ondelete="restrict")
	acquire_bank_id = fields.Many2one(comodel_name ='acquiring.bank', string="Banco Adquiriente", ondelete="restrict")
	code_categ_id = fields.Many2one(comodel_name ='code.category', string='Categoría comercial', ondelete="restrict")
	cluster_id = fields.Many2one(comodel_name ='segmentation.cluster', string='Cluster', ondelete="restrict")
	observation = fields.Text(string='Observaciones')
	wallet_associate_id = fields.Many2one(comodel_name ='wallet.associate', string='Código de centros comerciales', ondelete="restrict")
	chain_id = fields.Many2one(comodel_name ='code.chain', string="Código Cadena", ondelete="restrict")
	bank_segment_id = fields.Many2one(comodel_name='bank.segment', string="Banca o segmento que refiere", ondelete="restrict")
	mgr_regional_id = fields.Many2one(comodel_name='mgr.regional', string="Gerencia regional bancas", ondelete="restrict")
	regional_manager = fields.Many2one(comodel_name='res.users', string="Gerente Regional", ondelete="restrict")

	# seccion Documentos
	cedula = fields.Binary(string="Cedula de Identidad", attachment=True)
	rif = fields.Binary(string="R.I.F", attachment=True)
	contrato = fields.Binary(string="Terminación de contratos", attachment=True)

	commercial_register = fields.Binary(string="Registro Mercantil", attachment=True)
	commercial_reference = fields.Binary(string="Referencias comerciales", attachment=True)
	commercial_reference_2 = fields.Binary(string="Referencias comerciales", attachment=True)
	commercial_reference_3 = fields.Binary(string="Referencias comerciales", attachment=True)
	bank_certification = fields.Binary(string="Certificación Bancaria", attachment=True)
	authorization_payment_transfer = fields.Binary(string="Autorización para recibir pago por transferencia", attachment=True)
	parent_affiliated = fields.Char(string="Afiliado de empresa relacionada", help="Número de afiliación correspondiente a la compañia relacionada.")
	display_name = fields.Char(store=True)

	@api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'affiliated')
	def _compute_display_name(self):
		diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
		names = dict(self.with_context(**diff).name_get())
		for partner in self:
			partner.display_name = names.get(partner.id)

	@api.constrains('parent_id')
	def _constrains_parent_id(self):
		if self._context.get('import_file', False):
			if self.parent_id and self.parent_id.affiliated:
				self.parent_affiliated = self.parent_id.affiliated
			else:
				self.parent_affiliated = False

	@api.onchange('parent_id')
	def _onchange_parent_id(self):
		if self.parent_id and self.parent_id.affiliated:
			self.parent_affiliated = self.parent_id.affiliated
		else:
			self.parent_affiliated = False

	@api.constrains('parent_affiliated')
	def _constrains_parent_affiliated(self):
		if self._context.get('import_file', False) and self.parent_affiliated and (not self.parent_id or self.parent_id.affiliated != self.parent_affiliated):
			parent = self.search([('affiliated', '=', self.parent_affiliated)], limit=1)
			if parent:
				self.parent_id = parent
			else:
				raise exceptions.ValidationError("El numero de afiliación no concuerda con ningún cliente")

	@api.onchange('parent_affiliated')
	def _onchange_parent_affiliated(self):
		if self.parent_affiliated:
			parent = self.search([('affiliated', '=', self.parent_affiliated)], limit=1)
			if parent:
				self.parent_id = parent
			else:
				raise exceptions.ValidationError("El numero de afiliación no concuerda con ningún cliente")

	#Asignar el rif del contacto padre al contacto hijo automaticamente
	@api.onchange('parent_id')
	def _parent_onchange(self):
		self.vat = self.parent_id.vat
	
	#Al campo regional_manager se le asigna el lider del equipo de venta seleccionado 
	@api.onchange('team_id')
	def _regional_manager(self):
		self.regional_manager = self.team_id.user_id.id

	@api.onchange('affiliated')
	def _onchange_affiliated(self):
		if self.affiliated:
			self.affiliated = self.affiliated.lstrip("0")
			partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)])
			if len(partner) > 0:
				raise exceptions.ValidationError("Ya existe un contacto con el numero de Afiliado ingresado")
	
	def get_family_tree(self):
		root_partner = self
		while(root_partner.parent_id):
			root_partner = root_partner.parent_id
		return self._get_family_tree(root_partner)

	def _get_family_tree(self, root):
		family_tree = [root.id]
		for child in root.child_ids:
			if child.child_ids:
				family_tree += self._get_family_tree(child)
			else:
				family_tree += [child.id]
		return family_tree
		
	# #Al momento de crear
	# @api.model_create_multi
	# def create(self, vals_list):
	# 	result = super().create(vals_list)
	# 	for contact in result:
	# 		if not contact.bank_ids and (self.contact_type == '0' or self.contact_type == '1' or self.contact_type == '2'):
	# 			raise exceptions.ValidationError("Debe ingresar al menos una cuenta bancaria")
	# 		self.get_family_tree()
	# 	return result

	# #Al momento de editar
	# def write(self, vals):
	# 	result = super().write(vals)
	# 	if not self.bank_ids and (self.contact_type == '0' or self.contact_type == '1' or self.contact_type == '2'):
	# 		raise exceptions.ValidationError("Debe ingresar al menos una cuenta bancaria")
	# 	res = self.get_family_tree()
	# 	return result

	@api.onchange('company_type')
	def person_type(self):
		if self.company_type == 'person':
			self.people_type_company = False
		else:
			self.people_type_individual = False

	#quitar validacion de rif para contactos no domiciliados 
	@api.model
	def validate_rif(self, field_value):
		if (self.people_type_individual ==  'pnre') or (self.people_type_company == 'pjdo'):
			return super(Partner, self).validate_rif(field_value)

	region_domain = fields.Many2many('crm.region')

	@api.constrains('state_id')
	def set_region_and_domain(self):
		if self._context.get('import_file', False) and self.state_id:
			query = '''SELECT region FROM region_state WHERE state = ''' + str(self.state_id.id)
			cr = self._cr
			cr.execute(query)
			result = cr.dictfetchall()
			if len(result) == 1:
				self.region_id = result[0]['region']
				self.region_domain = [(6, 0, [result[0]['region']])]
			elif len(result) > 1:
				ids = list()
				for i in range(len(result)):
					ids.append(result[i]['region'])
				self.region_domain = [(6, 0, ids)]

	@api.onchange('state_id')
	def set_region_and_domain(self):
		if self.state_id:
			query = '''SELECT region FROM region_state WHERE state = ''' + str(self.state_id.id)
			cr = self._cr
			cr.execute(query)
			result = cr.dictfetchall()

			self.region_id = False
			self.region_domain = [(6, 0, [])]
			
			if len(result) == 1:
				self.region_id = result[0]['region']
				self.region_domain = [(4, result[0]['region'])]

			elif len(result) > 1:
				for i in range(len(result)):
					self.region_domain = [(4, result[i]['region'])]

	@api.constrains('region_id', 'bank_region_id')
	def check_region_id(self):
		if self.contact_type in ['0', '1'] and not self.region_id:
			raise exceptions.ValidationError('Región')
		if self.contact_type in ['0', '1'] and not self.bank_region_id:
			raise exceptions.ValidationError('Región bancaria')
