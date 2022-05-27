# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import ValidationError

class StockDeliveryOrder(models.AbstractModel):
	_name = 'report.stock_reports.sim_delivery_order'
	_description = 'Stock sim delivery report'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['stock.picking'].browse(docids)
		
		not_allowed = docs.filtered(lambda p: p.picking_type_code != 'incoming' or p.state not in ['assigned','done'])
		if not_allowed:
			raise ValidationError(_("""This document only can be printed if picking is a incoming operation and its state is assigned or done."""))
		
		footer = """
			CONDICIONES DE LA ORDEN DE SALIDA DE ACTIVOS Y MATERIALES / NOTA DE ENTREGA<br/>
			El presente documento constituye una autorización de Nativa a la empresa
			transportista CORPORACIÓN C.C.F.G., C.A. (TEALCA.), domiciliada en la ciudad
			de Caracas, inscrita en el Registro Único de Información Fiscal (R.I.F.)
			bajo él No. J-31498083-1, Documentos Mercantiles S.A (DOMESA) domiciliada en
			la ciudad de Caracas, inscrita en el Registro Unico de Informacion Fiscal (R.I.F.)
			bajo el No. J-00091991-7 o cualquier otra empresa que Nativa suscriba contratos
			de servicios para que realice el traslado de los equipos y periféricos aquí mencionados
			desde la sede Nativa hasta el centro de acopio de la trasportistas en el área
			metropolitana de Caracas, desde donde será despachado al interior del país.
		"""
		
		return {
			'docs': docs,
			'footer': footer,
			'model': self.env['report.stock_reports.sim_delivery_order']
		}

	def get_lines(self, move):
		if move:
			rows = ''
			tag = False
			columns = 4

			for i, lot_id in enumerate(move.move_line_ids.mapped('lot_id'), 1):

				if not tag:
					rows += '<tr>'
					tag = True
				
				rows += '<td>'+lot_id.name+'</td>'

				if i % columns == 0 and tag:
					rows += '</tr>'
					tag = False

			if tag: rows += '</tr>'

			return rows