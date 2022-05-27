from odoo import api, fields, models

class DeliveryWizardLine(models.TransientModel):
	_name = "request.keys.wizard.line"
	_description = 'MRP Picking Line'
	
	product_id = fields.Many2one('product.product', string='Product', readonly=True)
	quantity = fields.Float('quantity', digits='Product Unit of Measure')
	wizard_id = fields.Many2one('request.keys', 'wizard', invisible=True)

class RequestKeys(models.TransientModel):
    _name = 'request.keys'

    mrp_order_ids = fields.Many2many('mrp.production')
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén')
    picking_type_id = fields.Many2one('stock.picking.type', 
        domain="[('warehouse_id', '=', warehouse_id), ('is_key_operation', '=', True)]", string='Tipo de operación')
    product_ids = fields.One2many('request.keys.wizard.line', 'wizard_id', 'Lines')

    def action_confirm(self):
        self.ensure_one()
        picking_values = self._prepare_picking_values()
        picking = self.env['stock.picking'].create(picking_values)
        picking.action_confirm()
        return {
            'type': 'ir.actions.act_window',
            'name': picking.name,
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }
    
    @api.model
    def _prepare_picking_values(self):
        order = self.mrp_order_ids[0]
        return {
            'picking_type_id': self.picking_type_id.id,
            'origin': order.name,
            'immediate_transfer': False,
            'request_mrp_order_id': order.id,
            'company_id': order.company_id.id,
            'location_id': self.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
            'move_lines': [(0, 0, {
				'name': 'Production key',
				'location_id': self.picking_type_id.default_location_src_id.id,
				'location_dest_id': self.picking_type_id.default_location_dest_id.id,
				'product_id': line.product_id.id,
				'product_uom': line.product_id.uom_id.id,
				'product_uom_qty': line.quantity,
			}) for line in self.product_ids],
        }