from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class ProductionLot(models.Model):
	_inherit = 'stock.production.lot'

	name = fields.Char('Lot/Serial Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'), required=True, help="Unique Lot/Serial Number", tracking=True)
	terminal = fields.Char(string="Terminal", tracking=True)
	condition_id = fields.Many2one("condition.stock", string="Condition", tracking=True, ondelete="restrict")
	status_id = fields.Many2one("status.stock", string="Status", tracking=True, ondelete="restrict")
	partner_id = fields.Many2one("res.partner", string="Affiliate assigned", tracking=True)
	affiliated = fields.Char(string='Número de Afiliación')
	number_transactions = fields.Integer(string="Number of transactions")
	assembly_date = fields.Date(string="Assembly date", tracking=True)
	assembly_place = fields.Many2one('res.country', string="Assembly place", copy=False)
	production_line = fields.Char(string="Production line", tracking=True)
	battery_number = fields.Char(string="Battery number", tracking=True)
	application_version = fields.Many2one('application.versions', string="Application version", tracking=True, ondelete="restrict")
	key_version = fields.Many2one('product.product', string="Key version", tracking=True)
	sim_card = fields.Many2one('stock.production.lot', string="SIM card", tracking=True)
	network_operator_id = fields.Many2one('crm.company.pos', string='Operadora', tracking=True, readonly=True, related='sim_card.product_id.network_operator_id')
	communication_id = fields.Many2many(related='product_id.communication_id', readonly=True)
	is_wireless = fields.Boolean(compute='_compute_is_wireless')
	negotiation_type_id = fields.Many2one('crm.negotiation', string="Tipo de negociación", tracking=True, ondelete="restrict")
	length_stay = fields.Integer(compute='get_stay', help=_("The number of days the product has been in stock at the current warehouse."))
	current_location = fields.Many2one('stock.location', help=_("current location where the product is located"))
	warehouse_id = fields.Many2one('stock.warehouse')
	in_warehouse_date = fields.Date()
	product_type = fields.Selection(related='product_id.product_type', readonly=True)
	move_id = fields.Many2one('stock.move', 'Stock Move')
	tracking = fields.Selection(related='product_id.tracking')

	@api.constrains('sim_card')
	def _constrains_sim_card(self):
		if self.sim_card:
			lot_id = self.search([('sim_card', '=', self.sim_card.id), ('id', '!=', self.id)], limit=1)
			if lot_id:
				raise ValidationError(_("SIM card is already assigned to \nProduct: %s \nSerial/Lot: %s" % (lot_id.product_id.name, lot_id.name)))

	@api.depends('communication_id')
	def _compute_is_wireless(self):
		for lot_id in self:
			if lot_id.communication_id and 1 in lot_id.communication_id.mapped('type_code'):
				lot_id.is_wireless = True
			else:
				lot_id.is_wireless = False

	def calculate_terminal(self, serial):
		terminal = serial.upper()
		dict = {'A': '1', 'B': '2', 'D': '9', 'H': '3', 'K': '4', 'L': '5'}
		resul = ''
		for caracter in terminal:
			resul += dict.get(caracter, caracter)
		return resul

	@api.onchange('product_id')
	def _onchange_product(self):
		if self.product_id:
			self.terminal = self.calculate_terminal(self.name)

	@api.model_create_multi
	def create(self, vals_list):
		res = super().create(vals_list)
		condition_id = self.env['condition.stock'].search([('default','=',True)], limit=1)
		for lot in res:
			lot.terminal = self.calculate_terminal(lot.name)
			lot.condition_id = condition_id
		return res


	###############################################################################################
	#SEARCH
	###############################################################################################
	@api.onchange('partner_id')
	def _search_by_partner(self):
		"""Busca cliente por nombre"""
		if self.partner_id:
			self.affiliated = self.partner_id.affiliated

	@api.onchange('affiliated')
	def _search_by_affiliated(self):
		"""Busca cliente por afiliado"""
		if self.affiliated:
			partner_id = self.env['res.partner'].search([('affiliated','=',self.affiliated), ('contact_type','in', ['0','1'])], limit=1)
			if partner_id:
				self.partner_id = partner_id
			else:
				raise ValidationError(_("""El número de afiliado no pertenece a ningun contacto."""))

	# calculate the amount of days one product stay in a warehouse
	@api.depends('warehouse_id')
	def get_stay(self):
		for rec in self:
			if rec.current_location and rec.current_location.usage == 'internal' and rec.in_warehouse_date:
				rec.length_stay = (date.today() - rec.in_warehouse_date).days
			else:
				rec.length_stay = 0

	# this get the last location, that usualy belongs to a warehouse
	def get_father(self, son):
		if son.location_id.location_id:
			res = self.get_father(son.location_id)
		else:
			res = son
		return res