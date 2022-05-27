# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountReport(models.AbstractModel):
	_inherit = 'account.report'

	def _get_reports_buttons(self):
		if self.env.context.get('model') in ['account.aged.receivable', 'account.aged.payable'] and not 'USD' in self.env.context:
			return [
				{'name':_('Visualizar en Dólares'), 'sequence': 1, 'action': 'recalculate_to_usd'},
				{'name': _('Print Preview'), 'sequence': 2, 'action': 'print_pdf', 'file_export_type': _('PDF')},
				{'name': _('Export (XLSX)'), 'sequence': 3, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
				{'name':_('Save'), 'sequence': 10, 'action': 'open_report_export_wizard'},
			]
		else:
			return super(AccountReport, self)._get_reports_buttons()

	def recalculate_to_usd(self, options):
		return {
			'type': 'ir.actions.client',
			'name': _('En Dólares'),
			'tag': 'account_report',
			'context': {
				'model': self.env.context.get('model'),
				'USD': True
			}
		}