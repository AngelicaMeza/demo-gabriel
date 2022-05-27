from odoo import api, fields, models, _

class DeliveryWizard(models.TransientModel):
	_name = 'helpdesk.delivery.wizard'

	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', check_company=True, required=True)
	picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', required=True, check_company=True)
	location_id = fields.Many2one('stock.location', string='From', check_company=True, required=True)
	location_dest_id = fields.Many2one('stock.location', string='To', check_company=True, required=True)
	view_location_id = fields.Many2one(related='warehouse_id.view_location_id')

	ticket_id = fields.Many2one('helpdesk.ticket')
	region_id = fields.Many2one('crm.region', related='ticket_id.region_id')
	lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')
	product_id = fields.Many2one('product.product', related='lot_id.product_id', string='Product to deliver', readonly=True)

	@api.onchange('ticket_id')
	def _default_warehouse_id(self):
		if self.ticket_id:
			self.warehouse_id = False
			picking_list = self.ticket_id.delivery_picking_ids.ids + self.ticket_id.return_picking_ids.ids
			picking_id = self.env['stock.picking'].search([('id','in',picking_list),('state','in',['assigned','incorporated','done'])], order='create_date desc', limit=1) if picking_list else False

			if picking_id:
				self.warehouse_id = picking_id.picking_type_id.warehouse_id.id
			
			elif self.lot_id.move_id and self.lot_id.move_id.warehouse_id:
				self.warehouse_id = self.lot_id.move_id.warehouse_id
			
			else:
				warehouse_ids = self.env['stock.warehouse'].search([('company_id','=', self.company_id.id),('region','=', self.region_id.id)])
				if len(warehouse_ids) == 1: self.warehouse_id = warehouse_ids

	@api.onchange('warehouse_id')
	def _default_picking_type_id(self):
		self.picking_type_id = False
		if self.warehouse_id:
			picking_type_ids = self.env['stock.picking.type'].search([('warehouse_id','=',self.warehouse_id.id),('bills', '=', True)])
			if len(picking_type_ids) == 1:
				self.picking_type_id = picking_type_ids

	@api.onchange('picking_type_id')
	def _default_locations(self):
		if self.picking_type_id:
			self.location_id = self.picking_type_id.default_location_src_id
			self.location_dest_id = self.picking_type_id.default_location_dest_id
		else:
			self.location_id = False
			self.location_dest_id = False

	def create_picking(self):
		
		new_picking = self.env['stock.picking'].create({
			'state': 'draft',
			'partner_id': self.ticket_id.partner_id.id,
			'picking_type_id': self.picking_type_id.id,
			'origin': _('Ticket delivery: %s (#%s)') % (self.ticket_id.name, self.ticket_id.id),
			'location_id': self.location_id.id,
			'location_dest_id': self.location_dest_id.id,
			'move_lines': [(0, 0, {
				'name': 'Ticket delivery',
				'location_id': self.location_id.id,
				'location_dest_id': self.location_dest_id.id,
				'product_id': self.product_id.id,
				'product_uom': self.product_id.uom_id.id,
				'product_uom_qty': 1,
			})],
		})

		new_picking.message_post_with_view(
			'mail.message_origin_link',
			values={
				'self': new_picking,
				'origin': self.ticket_id
			},
			subtype_id=self.env.ref('mail.mt_note').id
		)

		self.ticket_id.delivery_picking_ids |= new_picking
		
		new_picking.action_confirm()
		new_picking.action_assign()

		return {
			'type': 'ir.actions.act_window',
			'name': _('Delivered Picking'),
			'res_model': 'stock.picking',
			'view_mode': 'form,tree',
			'res_id': new_picking.id,
		}