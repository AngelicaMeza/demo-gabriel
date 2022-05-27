# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DeliveryGuideReportPickingType(models.Model):
	_inherit = "stock.picking.type"

	print_delivery_guide = fields.Boolean()

class DeliveryGuideReportPicking(models.Model):
	_inherit = "stock.picking"

	package_number = fields.Integer()
	picking_type_report = fields.Boolean(related="picking_type_id.print_delivery_guide")

	def get_address(self):
		if self.partner_id:
			for child in self.partner_id.child_ids:
				if child.type == 'delivery':
					return child.street
				
			return self.partner_id.street

class StockDeliveryguide(models.AbstractModel):
	_name = 'report.stock_reports.delivery_guide'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['stock.picking'].browse(docids)
		
		not_allowed = docs.filtered(lambda p: not p.picking_type_id.print_delivery_guide or p.state not in ['assigned', 'incorporated','done'])
		if not_allowed:
			raise ValidationError(_("""The dispatch guide can only be printed if the type of operation allows it and if the operation is in the "prepared", "incorporated" or "performed" status.""")) # La guiá de despacho solo se puede imprimir si el tipo de operación lo permite y si la operación esta en los estados "preparado", "incorporado" o "realizado".
		return {
			'docs': docs,
		}
