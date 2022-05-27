# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _

class Inventory(models.Model):
	_inherit = "stock.inventory"
	_description = "Inventory"

	def action_validate(self):
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
				and qt.quantity > 0
			;""".format("', '".join(str(line.prod_lot_id.id) for line in self.line_ids if line.is_editable), self.env.company.id )
		self._cr.execute(query)
		result = self._cr.fetchall()
		if result:
			raise ValidationError(_("Los productos con seguimiento por serial sólo pueden tener 1 cantidad por empresa, usted está intentando añadir más.\nnúmeros de serie: {}".format(str([lot[0] for lot in result]))))

		return super(Inventory, self).action_validate()