from odoo import models, fields, api
from odoo.exceptions import ValidationError


class crm_type_negotiation(models.Model):
	_name = 'crm.negotiation'
	_description = 'Tipo de negociacion'

	name = fields.Char(string = "Tipo")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos tipos de negociación con el mismo nombre'),
	]

# Tipo de comunicaion
class crm_type_point_sale(models.Model):
	_name = 'crm.point.sale'
	_description = 'Tipo de punto de venta'

	name = fields.Char(string = "Tipo")
	type_code = fields.Integer(string="Código")
	active = fields.Boolean('Active', default=True)

	_sql_constraints=[('type_code_uniq', 'UNIQUE(type_code)', 'El código debe ser único')]
	
	@api.constrains('type_code')
	def _check__code(self):
		if self.type_code > 999 or self.type_code < 1:
			raise ValidationError('El código no puede ser cero (0) o tener mas de 3 dígitos')

# Operadora telefonica
class crm_company_pos(models.Model):
	_name = 'crm.company.pos'
	_description = 'Operadora telefonica'

	name = fields.Char(string = "Operadora")
	code = fields.Integer(string='Codigo', readonly=True, copy=False)
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('name_code_uniq', 'unique (name, code)', "Network operator already exist !!!"),
	]

	@api.model_create_multi
	def create(self, vals_list):
		res = super(crm_company_pos, self).create(vals_list)
		for rec in res:
			rec.code = self.env['ir.sequence'].next_by_code('network.operator')
		return res

class Event_name(models.Model):
	_name = 'event.name'
	_description = 'Nombre del evento'

	name = fields.Char(string = "Nombre del evento")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos eventos con el mismo nombre'),
	]

class crm_origin(models.Model):
	_name = 'crm.origin'
	_description = 'Origen'

	name = fields.Char(string = "Origen")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos origenes con el mismo nombre'),
	]