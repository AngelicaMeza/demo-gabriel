from odoo import models, fields


class segmentation_cluster(models.Model):
	_name = 'segmentation.cluster'
	_description = 'Segmentation'

	name = fields.Char(string = "Nombre")
	priority = fields.Integer('Prioridad')
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_priority', 'unique (priority)', "La prioridad ya fue asignada a otro cluster !"),
		('unique_name', 'unique (name)', "No pueden haber dos cluster con el mismo nombre !"),
	]

	def name_get(self):
		result = []
		for rec in self:
			if self._context.get('show_priority'):
				name = '%s - %s' % (rec.priority, rec.name)
			else:
				name = rec.name
			result.append((rec.id, name))
		return result

class code_category(models.Model):
	_name="code.category"
	_description = 'codigo y categoria'
	_rec_name = 'search_name'
	
	code = fields.Char(string="Código")
	name = fields.Char(string="Descripción de categoría")
	search_name = fields.Char()
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos categorías con el mismo nombre'),
		('unique_code', 'unique (code)', 'No pueden haber dos categorías con el mismo codigo'),
	]

	def name_get(self):
		result = []
		for account in self:
			account.search_name = account.code + ' ' + account.name 
			result.append((account.id, account.search_name ))
		return result

class code_chain(models.Model):
	_name = 'code.chain'
	_description = 'Codigo cadena'
	_rec_name = 'code'

	code = fields.Char(string='código')
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('code_wallet_uniq', 'unique (code)', "code already exists !"),
	]

class region(models.Model):
	_name = 'crm.region'
	_description = 'region'

	name = fields.Char(string='Nombre de región')
	states =fields.Many2many('res.country.state', 'region_state', 'region', 'state')
	active = fields.Boolean('Active', default=True)

class region(models.Model):
	_name = 'crm.bank.region'
	_description = 'bank region'

	name = fields.Char(string='Nombre de región')
	active = fields.Boolean('Active', default=True)

class territory(models.Model):
	_name = 'territory'
	_description = 'territorio'
	_rec_name = 'territory'

	territory = fields.Char(string = "Nombre")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_territory', 'unique (territory)', 'No pueden haber dos territorios con el mismo nombre'),
	]

	#Set breadcrumb

class uba(models.Model):
	_name = 'crm.uba'
	_description = 'Uba'
	_rec_name = 'code'

	code = fields.Char(string='Código')
	active = fields.Boolean('Active', default=True)
	
	_sql_constraints = [
		('code_uba_uniq', 'unique (code)', "code already exists !"),
	]

class wallet_associate(models.Model):
	_name = 'wallet.associate'
	_description = 'cartera asociada'
	_rec_name = 'wallet_associate'

	wallet_associate = fields.Char(string='Código')
	active = fields.Boolean('Active', default=True)
	
	_sql_constraints = [
		('wallet_associate_uniq', 'unique (wallet_associate)', "wallet associate already exists !"),
	]

class acquiring_bank(models.Model):
	_name = 'acquiring.bank'
	_description = 'banco adquirente'

	name = fields.Char(string= "Nombre")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos bancos con el mismo nombre'),
	]

class crm_bank_segment(models.Model):
	_name = 'bank.segment'
	_description = 'banca o segmento'

	name = fields.Char(string = "Nombre")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos banca o segmento con el mismo nombre'),
	]

class crm_mgr_regional(models.Model):
	_name = 'mgr.regional'
	_description = 'gerencia regional bancos'

	name = fields.Char(string = "Nombre")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_name', 'unique (name)', 'No pueden haber dos gerencias con el mismo nombre'),
	]