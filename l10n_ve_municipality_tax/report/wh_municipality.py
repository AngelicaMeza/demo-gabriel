# coding: utf-8

from odoo import models, api, _
from odoo.exceptions import UserError


class RepComprobanteMunicipal(models.AbstractModel):
	_name = 'report.l10n_ve_municipality_tax.template_wh_municipality_tax'

	@api.model
	def _get_report_values(self, docids, data=None):
		if not docids:
			raise UserError(_("Necesita seleccionar una retencion para imprimir."))
		docs = {'form': self.env['municipality.tax'].browse(docids)}

		if docs['form'].state == 'posted':
			return {
				'docs': docs['form'],
				'model': self.env['report.l10n_ve_municipality_tax.template_wh_municipality_tax'],
				'doc_model': self.env['report.l10n_ve_municipality_tax.template_wh_municipality_tax'],
			}
		else:
			raise UserError(_("La Retencion debe estar en estado Realizado para poder generar su Comprobante"))