# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	is_key_operation = fields.Boolean('¿Es una operación de movimiento de llaves?')
	is_sim_operation = fields.Boolean('¿Es una operación que solicita SIM?')
	is_sim_operation_move = fields.Boolean('¿Es una operación de movimiento de SIM?')
	sim_operation_type = fields.Many2one('stock.picking.type', string='Tipo de operación para solicitud de SIM', domain='[("is_sim_operation_move", "=", True)]')


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	is_sim_operation = fields.Boolean(compute='_compute_is_sim_operation')
	sim_picking_id = fields.Many2one('stock.picking', string='Operación que solicita SIM')
	sim_picking_ids = fields.One2many('stock.picking', 'sim_picking_id', string='Solicitudes de SIM', copy=False)
	sim_picking_count = fields.Integer(compute='_compute_sim_picking_count', string='Transferencias')
	sim_transfer_ids = fields.Many2many('stock.picking', 'picking_transfer_sim_rel', 'picking_origin_id', 'picking_request_id', string='Transferencias de SIM', copy=False)
	available_sim_lot_ids = fields.Many2many('stock.production.lot', compute='_compute_available_sim_lot_ids')
	sim_operation_message = fields.Char(compute='_compute_sim_operation_message')

	courier_id = fields.Many2one('stock.courier', string='Courier', ondelete="restrict")
	courier_guide = fields.Char(string='Courier guide')
	restrict_user = fields.Boolean(compute='_im_restrict_user')

	def _im_restrict_user(self):
		if self.env.user.has_group('stock_customization.stock_restrict_picking_lines'): 
			self.restrict_user = True
		else:
			self.restrict_user = False

	@api.depends('picking_type_id', 'move_line_ids')
	def _compute_is_sim_operation(self):
		"""Set is_sim_operation in True if product_id is a POS and a wireless network devices."""
		for picking in self:
			if(
				picking.picking_type_id.is_sim_operation and\
				picking.state in ['assigned', 'incorporated'] and\
				any(m.is_sim_operation for m in picking.move_line_ids)
			):
				picking.is_sim_operation = True
			else:
				picking.is_sim_operation = False

	@api.depends('sim_transfer_ids', 'move_line_ids')
	def _compute_available_sim_lot_ids(self):
		for picking in self:
			picking.available_sim_lot_ids = [(5, 0, 0)]
			if picking.sim_transfer_ids:
				all_sim_lot_ids = picking.sim_transfer_ids.move_line_ids.lot_id
				taken_sim_lot_ids = picking.move_line_ids.sim_lot_id
				picking.available_sim_lot_ids = all_sim_lot_ids - taken_sim_lot_ids

	@api.depends('sim_picking_ids')
	def _compute_sim_picking_count(self):
		for picking in self:
			picking.sim_picking_count = len(picking.sim_picking_ids)
	
	@api.depends('available_sim_lot_ids', 'sim_transfer_ids', 'state')
	def _compute_sim_operation_message(self):
		for picking in self:
			if picking.state != 'assigned' or not picking.sim_transfer_ids:
				picking.sim_operation_message = ''
				continue

			lots = picking.available_sim_lot_ids
			lines_without_sim = picking.move_line_ids.filtered(lambda l: l.is_sim_operation and not l.sim_lot_id)
			
			length_lots = len(lots)
			length_lines = len(lines_without_sim)

			message = ''
			if length_lots == 0 and length_lines:
				message = 'Hay %d equipo sin SIM asignado' %(length_lines)
			elif length_lots > 0:
				message = 'Quedan %d SIM sin asignar' %(length_lots)
			
			picking.sim_operation_message = message
	
	def action_view_sim_pickings(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'Solicitudes de SIM (%s)' %self.name,
			'res_model': 'stock.picking',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', self.sim_picking_ids.ids)]
		}

	def action_request_SIM(self):
		self.ensure_one()
		if self.is_sim_operation:
			picking = self.create({
				'picking_type_id': self.picking_type_id.sim_operation_type.id,
				'origin': self.name,
				'immediate_transfer': False,
				'sim_picking_id': self.id,
				'company_id': self.company_id.id,
				'location_id': self.picking_type_id.sim_operation_type.default_location_src_id.id,
				'location_dest_id': self.picking_type_id.sim_operation_type.default_location_dest_id.id,
			})

			return {
				'type': 'ir.actions.act_window',
				'name': picking.name,
				'res_model': 'stock.picking',
				'view_mode': 'form',
				'res_id': picking.id
			}
	
	def action_assing_sim(self):
		self.ensure_one()
		if self.available_sim_lot_ids:
			lines = self.move_line_ids.filtered(lambda l: l.is_sim_operation and not l.sim_lot_id)
			for lot, line in zip(self.available_sim_lot_ids, lines):
				if line.product_id.tracking == 'serial':
					line.sim_lot_id = lot

	def button_validate(self):
		self.ensure_one()
		if self.location_id.usage != 'internal':
			lots = "', '".join(str(lot.id) for lot in self.move_line_ids.mapped('lot_id'))
			if lots == '':
				lots = '0'
			query="""
				SELECT 
					lot.name
				FROM 
					public.stock_quant as qt 
					JOIN public.stock_location as lt ON lt.id = qt.location_id
					JOIN public.product_product as pp ON pp.id = qt.product_id
					JOIN public.product_template as pt ON pt.id = pp.product_tmpl_id
					JOIN public.stock_production_lot as lot ON lot.id = qt.lot_id
				WHERE
					lt.usage = 'internal' 
					and pt.tracking = 'serial'
					and qt.lot_id in ('{}')
					and qt.company_id = '{}'
					and qt.quantity >0
				;""".format(lots, str(self.company_id.id))
			self._cr.execute(query)
			result = self._cr.fetchall()
			if result:
				raise ValidationError(_("Los productos con seguimiento por serial sólo pueden tener 1 cantidad por empresa, usted está intentando añadir más.\nnúmeros de serie: {}".format(str([lot[0] for lot in result]))))
				# raise ValidationError(_("The products with serial tracking only can have 1 quantity per company, you are trying to add more\nSerial numbers: {}".format(str([lot[0] for lot in result]))))

		res = super(StockPicking, self).button_validate()

		#Escribe el lote de SIM seleccionado en el lote del producto
		if self.is_sim_operation: self.move_line_ids.validate_sim_operations()

		#Asigna informacion de producion y ensamblaje al lote
		for move in self.move_ids_without_package: move.confirm_detailed_operations()

		return res