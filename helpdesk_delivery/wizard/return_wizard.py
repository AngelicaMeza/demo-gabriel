# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ReturnWizard(models.TransientModel):
	_name = 'helpdesk.return.wizard'
	_description = 'Return wizard'

	company_id = fields.Many2one('res.company', string='Company', readonly=True)
	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
	picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', required=True, check_company=True)
	location_id = fields.Many2one(related='lot_id.current_location')
	location_dest_id = fields.Many2one(related='picking_type_id.default_location_dest_id', readonly=True)
	
	ticket_id = fields.Many2one('helpdesk.ticket')
	region_id = fields.Many2one(related='ticket_id.region_id')
	lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial number', readonly=True)
	product_id = fields.Many2one(related='lot_id.product_id', string='Product to return', readonly=True)

	@api.onchange('ticket_id')
	def _default_warehouse_id(self):
		if self.ticket_id:
			
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
			picking_type_ids = self.env['stock.picking.type'].search([('warehouse_id','=',self.warehouse_id.id),('code','=','incoming')])
			if len(picking_type_ids) == 1:
				self.picking_type_id = picking_type_ids

	def create_return_picking(self):

		new_picking = self.env['stock.picking'].create({
			'state': 'draft',
			'partner_id': self.ticket_id.partner_id.id,
			'picking_type_id': self.picking_type_id.id,
			'origin': _('Ticket return: %s (#%s)') % (self.ticket_id.name, self.ticket_id.id),
			'location_id': self.location_id.id,
			'location_dest_id': self.location_dest_id.id,
			'move_lines': [(0, 0, {
				'name': 'Ticket delivery',
				'location_id': self.location_id.id,
				'location_dest_id': self.location_dest_id.id,
				'product_id': self.lot_id.product_id.id,
				'product_uom': self.lot_id.product_id.uom_id.id,
				'product_uom_qty': 1,
				'origin_returned_move_id': self.lot_id.move_id and self.lot_id.move_id.id or False,
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

		new_picking.action_confirm()
		new_picking.action_assign()

		self.ticket_id.return_picking_ids |= new_picking
		new_picking.move_line_ids.lot_id = self.lot_id.id

		return {
			'type': 'ir.actions.act_window',
			'name': _('Return Orders'),
			'res_model': 'stock.picking',
			'view_mode': 'form,tree',
			'res_id': new_picking.id,
		}