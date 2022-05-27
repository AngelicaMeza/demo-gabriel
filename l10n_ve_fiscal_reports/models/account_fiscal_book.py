# -*- coding: utf-8 -*-

import io
from odoo import models, api, fields, _
from odoo.tools.misc import xlsxwriter
from odoo.tools.misc import format_date

NUMBER = 'number text-right text-nowrap'
TEXT = 'text-center text-nowrap'

class AccountFiscalBook(models.AbstractModel):
	_name = "account.fiscal.book"
	_description = "Venezuelan Fiscal Books"
	_inherit = "account.report"
	_order = "date asc"

	filter_date = {'mode': 'range', 'filter': 'this_month'}

	@api.model
	def _get_fiscal_book_lines(self, options):
		query = ("""
			SELECT
				account_move.id AS id,
				account_move.name AS move_name,
				CASE 
					WHEN account_move.type IN ('out_invoice', 'out_refund') THEN account_move.date
					WHEN account_move.type IN ('in_invoice', 'in_refund') THEN account_move.invoice_date
				END AS date,
				res_partner.vat AS partner_vat,
				res_partner.name AS partner_name,
				UPPER(COALESCE(res_partner.people_type_company, res_partner.people_type_individual)) AS person_type,
				account_move.nro_ctrl AS control_number,
				CASE 
					WHEN account_move.type = 'out_invoice' AND account_move.debit_origin_id IS NULL THEN SPLIT_PART(account_move.name, '/', 3)
					WHEN account_move.type = 'in_invoice' AND account_move.debit_origin_id IS NULL THEN account_move.supplier_invoice_number
				END AS invoice,
				CASE 
					WHEN account_move.type = 'out_refund' THEN SPLIT_PART(account_move.name, '/', 3)
					WHEN account_move.type = 'in_refund' THEN account_move.supplier_invoice_number
				END AS credit_note,
				CASE 
					WHEN account_move.type = 'out_invoice' AND account_move.debit_origin_id IS NOT NULL THEN SPLIT_PART(account_move.name, '/', 3)
					WHEN account_move.type = 'in_invoice' AND account_move.debit_origin_id IS NOT NULL THEN account_move.supplier_invoice_number
				END AS debit_note,
				CASE 
					WHEN account_move.type IN ('out_invoice', 'out_refund') THEN SPLIT_PART(affected_move.name, '/', 3)
					WHEN account_move.type IN ('in_invoice', 'in_refund') THEN affected_move.supplier_invoice_number
				END AS affected_invoice,
				account_move.nro_planilla_impor AS nro_planilla_impor,
				account_move.nro_expediente_impor AS import_file_number,
				CASE
					WHEN account_move.type IN ('out_invoice', 'out_refund') AND account_move.state = 'cancel' THEN 'ANU-03'
					WHEN account_move.type IN ('in_invoice', 'out_invoice') AND account_move.debit_origin_id IS NULL THEN 'REG-01'
					WHEN account_move.type IN ('in_refund', 'out_refund') OR ( account_move.type IN ('in_invoice', 'out_invoice') AND account_move.debit_origin_id IS NOT NULL ) THEN 'COM-02'
				END AS trans_type,
				SUM(CASE WHEN account_move_line.tax_line_id IS NULL AND account_move_line.account_internal_type IN ('receivable', 'payable') THEN ABS(account_move_line.balance) ELSE 0.0 END) AS amount_total,
				SUM(CASE WHEN account_move_line.tax_line_id IS NULL AND account_move_line.account_internal_type = 'other' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS tax_base_exempt,
				0.0 AS tax_base_untaxed,""" + ','.join(["""
				SUM(CASE WHEN account_move.nro_planilla_impor IS NULL AND account_tax.tax_type = '{i}' THEN account_move_line.tax_base_amount ELSE 0.0 END) AS tax_base_{i},
				MAX(TO_CHAR(CASE WHEN account_move.nro_planilla_impor IS NULL AND account_tax.tax_type = '{i}' THEN account_tax.amount ELSE 0 END, '999%%')) AS tax_percent_{i},
				SUM(CASE WHEN account_move.nro_planilla_impor IS NULL AND account_tax.tax_type = '{i}' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS tax_balance_{i},
				SUM(CASE WHEN account_move.nro_planilla_impor IS NOT NULL AND account_tax.tax_type = '{i}' THEN account_move_line.tax_base_amount ELSE 0.0 END) AS import_tax_base_{i},
				MAX(TO_CHAR(CASE WHEN account_move.nro_planilla_impor IS NOT NULL AND account_tax.tax_type = '{i}' THEN account_tax.amount ELSE 0 END, '999%%')) AS import_tax_percent_{i},
				SUM(CASE WHEN account_move.nro_planilla_impor IS NOT NULL AND account_tax.tax_type = '{i}' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS import_tax_balance_{i}""".format(i=i) for i in ['general', 'reduced', 'additional']]) + """,
				account_wh_iva.number AS wh_iva_number,
				COALESCE(account_wh_iva.total_tax_ret, 0.0) AS total_tax_ret,
				TO_CHAR(COALESCE(account_wh_iva.withholding_rate, 0), '999%%') AS wh_iva_withholding_rate,
				account_wh_iva.date_ret AS wh_iva_date_ret,
				CASE WHEN account_move.state = 'cancel' OR account_move.date NOT BETWEEN %(date_from)s AND %(date_to)s THEN 0 ELSE 1 END AS sign
			FROM account_move
			JOIN res_partner ON res_partner.id = account_move.partner_id
			JOIN account_move_line ON 
				account_move_line.move_id = account_move.id AND
				account_move_line.price_subtotal = account_move_line.price_total
			LEFT JOIN account_tax ON account_tax.id = account_move_line.tax_line_id AND account_tax.type_tax_use = %(type_tax_use)s
			LEFT JOIN account_wh_iva ON
				account_wh_iva.id = account_move.wh_iva_id AND
				account_wh_iva.date_ret BETWEEN %(date_from)s AND %(date_to)s AND
				account_wh_iva.state = 'done'
			LEFT JOIN account_move affected_move ON affected_move.id = account_move.debit_origin_id OR affected_move.id = account_move.reversed_entry_id
			WHERE
				(
					account_move.date BETWEEN %(date_from)s AND %(date_to)s OR
					account_wh_iva.date_ret BETWEEN %(date_from)s AND %(date_to)s
				) AND
				account_move.type = ANY(%(type)s) AND
				account_move.state = ANY(%(move_state)s) AND
				account_move.company_id = {company_id} AND
				account_move.exclude_from_fiscal_book = FALSE
			GROUP BY
				account_move.id, res_partner.id, affected_move.id, account_wh_iva.id
		""").format(company_id=self.env.company.id)

		if options['book_type'] == 'sale':
			query += ' ORDER BY account_move.nro_ctrl ASC '
		elif options['book_type'] == 'purchase':
			query += ' ORDER BY account_move.invoice_date ASC '

		if options.get('lines_offset') and options.get('lines_remaining', 0) > 0 and not self._context.get('print_mode'):
			query += ' OFFSET %s LIMIT %s ' % (int(options['lines_offset']), self.MAX_LINES)

		params = {
			'type_tax_use': options['book_type'],
			'date_from': options['date']['date_from'],
			'date_to': options['date']['date_to'],
			'type': options['type'],
			'move_state': options['move_state']
		}

		self._cr.execute(self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding))
		return self._cr.dictfetchall()

	@api.model
	def _get_total_sum(self, options):
		query = ("""
			SELECT
				SUM(aml.amount_total * aml.sign) AS amount_total,
				SUM(aml.total_base_exempt * aml.sign) AS tax_base_exempt,""" + ','.join(["""
				SUM(aml.total_base_{i} * aml.sign) AS tax_base_{i},
				SUM(aml.total_balance_{i} * aml.sign) AS tax_balance_{i},
				SUM(aml.import_total_base_{i} * aml.sign) AS import_tax_base_{i},
				SUM(aml.import_total_balance_{i} * aml.sign) AS import_tax_balance_{i}""".format(i=i) for i in ['general', 'reduced', 'additional']]) + """,
				SUM(COALESCE(account_wh_iva.total_tax_ret, 0.0)) AS total_tax_ret
			FROM account_move
			JOIN LATERAL(
				SELECT
					account_move_line.move_id,
					SUM(CASE WHEN account_move_line.tax_line_id IS NULL AND account_move_line.account_internal_type IN ('receivable', 'payable') THEN ABS(account_move_line.balance) ELSE 0.0 END) AS amount_total,
					SUM(CASE WHEN account_move_line.tax_line_id IS NULL AND account_move_line.account_internal_type = 'other' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS total_base_exempt,""" + ','.join(["""
					SUM(CASE WHEN account_move.nro_planilla_impor IS NULL AND account_tax.tax_type = '{i}' THEN account_move_line.tax_base_amount ELSE 0.0 END) AS total_base_{i},
					SUM(CASE WHEN account_move.nro_planilla_impor IS NULL AND account_tax.tax_type = '{i}' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS total_balance_{i},
					SUM(CASE WHEN account_move.nro_planilla_impor IS NOT NULL AND account_tax.tax_type = '{i}' THEN account_move_line.tax_base_amount ELSE 0.0 END) AS import_total_base_{i},
					SUM(CASE WHEN account_move.nro_planilla_impor IS NOT NULL AND account_tax.tax_type = '{i}' THEN ABS(account_move_line.balance) ELSE 0.0 END) AS import_total_balance_{i}""".format(i=i) for i in ['general', 'reduced', 'additional']]) + """,
					CASE WHEN account_move.type IN ('in_refund', 'out_refund') THEN -1 ELSE 1 END AS sign
				FROM account_move_line
				LEFT JOIN account_tax ON account_tax.id = account_move_line.tax_line_id AND account_tax.type_tax_use = %(type_tax_use)s
				WHERE
					account_move_line.move_id = account_move.id AND
					account_move_line.price_subtotal = account_move_line.price_total
				GROUP BY account_move_line.move_id
			) AS aml ON aml.move_id = account_move.id
			LEFT JOIN account_wh_iva ON
				account_wh_iva.id = account_move.wh_iva_id AND
				account_wh_iva.date_ret BETWEEN %(date_from)s AND %(date_to)s AND
				account_wh_iva.state = 'done'
			WHERE
				account_move.date BETWEEN %(date_from)s AND %(date_to)s AND
				account_move.type = ANY(%(type)s) AND
				account_move.state = 'posted' AND
				account_move.company_id = {company_id} AND
				account_move.exclude_from_fiscal_book = FALSE
		""").format(company_id=self.env.company.id)

		params = {
			'type_tax_use': options['book_type'],
			'date_from': options['date']['date_from'],
			'date_to': options['date']['date_to'],
			'type': options['type']
		}

		self._cr.execute(self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding))
		return self._cr.dictfetchall()

	def _get_columns_header(self):
		return [
			{'name': '', 'class': ''},
			{'name': _('Nro. Operación'), 'class': TEXT},
			{'field': 'date', 'name': _('Fecha Emisión Documento'), 'class': 'date'},
			{'field': 'partner_vat', 'name': _('Nro. de Identificación Fiscal'), 'class': TEXT},
			{'field': 'partner_name', 'name': _('Nombre o Razón Social'), 'class': TEXT},
			{'field': 'person_type', 'name': _('Tipo Persona'), 'class': TEXT},
			{'field': 'control_number', 'name': _('Nro. de Control'), 'class': TEXT},
			{'field': 'invoice', 'name': _('Nro. de Factura'), 'class': TEXT},
			{'field': 'credit_note', 'name': _('Nro. Nota de Crédito'), 'class': TEXT},
			{'field': 'debit_note', 'name': _('Nro. Nota de Débito'), 'class': TEXT},
			{'field': 'affected_invoice', 'name': _('Nro. Factura Afectada'), 'class': TEXT},
			{'field': 'trans_type', 'name': _('Tipo de Transacción'), 'class': TEXT}
		]

	def _get_columns_tax_groups(self):
		return [
			{'field': 'amount_total', 'name': _('Total Incluyendo IVA'), 'class': NUMBER, 'type': 'base', 'group': 'total'},
			{'field': 'tax_base_exempt', 'name': _('Exentas o No Gravadas'), 'class': NUMBER, 'type': 'base', 'group': 'exempt'},
			{'field': 'tax_base_untaxed', 'name': _('Exoneradas o Sin derecho a crédito Fiscal'), 'class': NUMBER, 'type': 'base', 'group': 'untaxed'},
			{'field': 'tax_base_general', 'name': _('Base Imponible Alícuota General'), 'class': NUMBER, 'type': 'base', 'group': 'general'},
			{'field': 'tax_percent_general', 'name': _('% Alícuota General'), 'class': TEXT, 'type': '', 'group': 'general'},
			{'field': 'tax_balance_general', 'name': _('Impuesto (I.V.A) Alícuota General'), 'class': NUMBER, 'type': 'tax', 'group': 'general'},
			{'field': 'tax_base_reduced', 'name': _('Base Imponible Alícuota Reducida'), 'class': NUMBER, 'type': 'base', 'group': 'reduced'},
			{'field': 'tax_percent_reduced', 'name': _('% Alícuota Reducida'), 'class': TEXT, 'type': '', 'group': 'reduced'},
			{'field': 'tax_balance_reduced', 'name': _('Impuesto (I.V.A) Alícuota Reducida'), 'class': NUMBER, 'type': 'tax', 'group': 'reduced'},
			{'field': 'tax_base_additional', 'name': _('Base Imponible Alícuota Adicional'), 'class': NUMBER, 'type': 'base', 'group': 'additional'},
			{'field': 'tax_percent_additional', 'name': _('% Alícuota Adicional'), 'class': TEXT, 'type': '', 'group': 'additional'},
			{'field': 'tax_balance_additional', 'name': _('Impuesto (I.V.A) Alícuota Adicional'), 'class': NUMBER, 'type': 'tax', 'group': 'additional'},
			{'field': 'wh_iva_number', 'name': _('Nro. de Comprobante'), 'class': TEXT, 'type': 'text', 'group': 'account_wh_iva'},
			{'field': 'total_tax_ret', 'name': _('IVA Retenido'), 'class': NUMBER, 'type': 'tax', 'group': 'account_wh_iva'},
		]

	@api.model
	def _get_columns_name(self, options):
		return self._get_columns_header() + self._get_columns_tax_groups()

	@api.model
	def _get_lines(self, options, line_id=None):

		date_from = fields.Date.from_string(options['date']['date_from'])
		fiscal_book_lines = self._get_fiscal_book_lines(options)
		header_format = self._get_columns_header()
		tax_format = self._get_columns_tax_groups()
		lines = []
		
		if not fiscal_book_lines:
			return lines

		offset = int(options.get('lines_offset', 0))
		load_more_remaining = options.get('lines_remaining') and int(options['lines_remaining']) or len(fiscal_book_lines)
		load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES

		for item, record in enumerate(fiscal_book_lines, offset+1):
			
			columns = [{'name': item}]

			for column in header_format[2:] + tax_format:
				value = record.get(column['field'])

				if column.get('type') in ['base', 'tax']:
					if not column['field'] == 'total_tax_ret' or record['date'] >= date_from:
						value *= record['sign']
					value = self.format_value(value)

				if 'date' in column['class']:
					value = format_date(self.env, value)

				columns.append({'name': value})

			lines.append({
				'id': record['id'],
				'name': record['move_name'],
				'columns': columns,
				'caret_options': 'account.move',
				'model': 'account.move',
			})

			load_more_remaining -= 1
			load_more_counter -= 1
			if load_more_counter == 0: break

		if load_more_remaining > 0:
			lines.append({
				'id': 'loadmore_%s' % load_more_remaining,
				'offset': item,
				'remaining': load_more_remaining,
				'class': 'o_account_reports_load_more text-center',
				'name': _('Load more... (%s remaining)') % load_more_remaining,
				'colspan': 7,
				'columns': [],
			})

		if not line_id:
			TOTALS = self._get_total_sum(options)
			TOTAL_LINE = [{'name': self.format_value(abs(TOTALS[0].get(column['field'], 0.0)), blank_if_zero=True)} for column in tax_format]
			lines.append({'id': 'total_line', 'columns': [{'name': _('Totals')}] + TOTAL_LINE, 'colspan': len(header_format) - 1, 'level': 2})
			if not self._context.get('print_mode'):
				lines += self._get_resume_lines(options, TOTALS[0])

		return lines

	def _get_resume_lines(self, options, TOTALS):
		lines = [{'id': 'blank_space', 'columns': []}]
		lines.append({
			'id': 'resume',
			'name': _('RESUMEN LIBRO FISCAL DE VENTAS'),
			'columns': [{'name': _('BASE IMPONIBLE')}, {'name': _('%s FISCAL' % options['strings']['resume_tax'].upper())}],
			'level': 2
		})

		resume_type = options['strings']['resume_type']

		resume_lines = [
			{'name': resume_type + ' internas exentas o no gravadas', 'base': 0.0},
			{'name': resume_type + ' internas exoneradas o sin derecho a crédito fiscal', 'base': TOTALS['tax_base_exempt']},
			{'name': resume_type + ' internas gravadas por alícuota general', 'base': TOTALS['tax_base_general'], 'tax': TOTALS['tax_balance_general']},
			{'name': resume_type + ' internas gravadas por alícuota reducida', 'base': TOTALS['tax_base_reduced'], 'tax': TOTALS['tax_balance_reduced']},
			{'name': resume_type + ' internas gravadas por alícuota general más alícuota adicional', 'base': TOTALS['tax_base_additional'], 'tax': TOTALS['tax_balance_additional']},
		]

		if options['book_type'] == 'purchase':
			resume_lines += [
				{'name': _('Importaciones gravadas alícuota general'), 'base': TOTALS['import_tax_base_general'], 'tax': TOTALS['import_tax_balance_general']},
				{'name': _('Importaciones gravadas por alícuota reducida'), 'base': TOTALS['import_tax_base_reduced'], 'tax': TOTALS['import_tax_balance_reduced']},
				{'name': _('Importaciones gravadas por alícuota general más adicional'), 'base': TOTALS['import_tax_base_additional'], 'tax': TOTALS['import_tax_balance_additional']}
			]

		GLOBAL_BASE = 0.0
		GLOBAL_TAX = 0.0
		for line in resume_lines: # ignore total and withholding
			base = line.get('base', 0.0)
			tax = line.get('tax', 0.0)
			GLOBAL_BASE += base
			GLOBAL_TAX += tax
			lines.append({
				'id': line['name'],
				'name': line['name'],
				'columns': [
					{'name': self.format_value(base), 'class': NUMBER},
					{'name': self.format_value(tax), 'class': NUMBER}
				]
			})

		# GLOBAL LINE
		lines.append({
			'id': 'global',
			'name': 'Total '+options['strings']['resume_type']+' y '+options['strings']['resume_tax']+' fiscales',
			'style': 'font-weight: bold;',
			'level': 2,
			'columns': [
				{'name': self.format_value(GLOBAL_BASE), 'class': NUMBER},
				{'name': self.format_value(GLOBAL_TAX), 'class': NUMBER}
			],
		})

		# WITHHOLDING LINE
		lines.append({
			'id': 'account_wh_iva',
			'name': _('Total IVA retenido'),
			'style': 'font-weight: bold;',
			'level': 2,
			'columns': [
				{'name': self.format_value(0.0), 'class': NUMBER},
				{'name': self.format_value(TOTALS['total_tax_ret']), 'class': NUMBER}
			],
		})

		return lines

	def _get_table(self, options):
		return self.get_header(options), self._get_lines(options)

	def get_xlsx(self, options, response=None):
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory': True, 'strings_to_formulas': False,})
		sheet = workbook.add_worksheet(self._get_report_name())

		date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
		default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
		title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'bottom': 1})
		bold_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12})

		#XLSX HEADER
		partner_id = self.env.company.partner_id
		sheet.merge_range(0, 0, 0, 10, 'Compañia: '+partner_id.name, bold_style)
		sheet.merge_range(1, 0, 1, 5, 'RIF.: '+partner_id.vat, bold_style)
		sheet.merge_range(2, 0, 2, 10, 'Dirección: '+partner_id.contact_address.replace('\n', ' '), bold_style)
		sheet.merge_range(3, 0, 3, 5, self._get_report_name().upper(), bold_style)
		sheet.merge_range(4, 0, 4, 2, 'Desde: '+options['date']['date_from'], bold_style)
		sheet.merge_range(4, 3, 4, 5, 'Hasta: '+options['date']['date_to'], bold_style)
		y_offset = 6
		
		headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

		# Add headers
		for header in headers:
			x_offset = 0
			for column in header[1:]:
				column_name_formated = column.get('name', '')
				sheet.merge_range(y_offset, x_offset, y_offset, x_offset + 1, column_name_formated, title_style)
				x_offset += 2
			y_offset += 1

		# Add lines
		for line in lines:
			style = col1_style = default_style
			x_offset = 0

			if line.get('level') == 2:
				style = title_style
				col1_style = style
			
			if line.get('class') == 'font-weight: bold;':
				style = bold_style
				col1_style = style

			if 'caret_options' not in line and not line.get('id') == 'total_line':
				cell_type, cell_value = self._get_cell_type_value(line)
				sheet.merge_range(y_offset, 0, y_offset, 1, cell_value, col1_style)
				x_offset += 2

			colspan = line.get('colspan') and line['colspan'] -1 or 0
			colspan *= 2

			for column in line['columns']:
				cell_type, cell_value = self._get_cell_type_value(column)
				if cell_type == 'date':
					sheet.write_datetime(y_offset, x_offset, cell_value, date_default_style)
				else:
					sheet.merge_range(y_offset, x_offset + colspan, y_offset, x_offset + colspan + 1, cell_value, style)
				x_offset += 2
			y_offset += 1

		TOTALS = self._get_total_sum(options)
		for line in self._get_resume_lines(options, TOTALS[0]):
			style = col1_style = default_style
			x_offset = 0

			if line.get('level') == 2:
				style = title_style
				col1_style = style
			
			if line.get('class') == 'font-weight: bold;':
				style = bold_style
				col1_style = style

			if 'caret_options' not in line and not line.get('id') == 'total_line':
				cell_type, cell_value = self._get_cell_type_value(line)
				sheet.merge_range(y_offset, 0, y_offset, 7, cell_value, col1_style)
				x_offset += 8

			for column in line['columns']:
				cell_type, cell_value = self._get_cell_type_value(column)
				sheet.merge_range(y_offset, x_offset, y_offset, x_offset + 1, cell_value, style)
				x_offset += 2
			y_offset += 1

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file

	@api.model
	def _resolve_caret_option_document(self, model, res_id, document):
		if self._name in ('sale.fiscal.book', 'purchase.fiscal.book'):
			return self.env[model].browse(res_id)
		else:
			return super(AccountFiscalBook, self)._resolve_caret_option_document(model, res_id, document)


class AccountSaleFiscalBook(models.AbstractModel):
	_name = "sale.fiscal.book"
	_description = "Sale Fiscal Book"
	_inherit = "account.fiscal.book"

	@api.model
	def _get_report_name(self):
		return _("Sale Fiscal Book")

	def _get_options(self, previous_options=None):
		options = super(AccountSaleFiscalBook, self)._get_options(previous_options)
		options.update({
			'book_type': 'sale',
			'type': ['out_invoice', 'out_refund'],
			'move_state': ['posted', 'cancel'],
			'strings': {
				'resume_type': _('Ventas'),
				'resume_tax': _('Débito')
			},
		})
		return options

	def _get_columns_tax_groups(self):
		tax_groups = super(AccountSaleFiscalBook, self)._get_columns_tax_groups()
		tax_groups.append({'field': 'wh_iva_date_ret', 'name': _('Fecha del Comprobante'), 'class': 'date', 'type': '', 'group': 'account_wh_iva'})
		return tax_groups


class AccountPurchaseFiscalBook(models.AbstractModel):
	_name = "purchase.fiscal.book"
	_description = "Purchase Fiscal Book"
	_inherit = "account.fiscal.book"

	@api.model
	def _get_report_name(self):
		return _("Purchase Fiscal Book")

	def _get_options(self, previous_options=None):
		options = super(AccountPurchaseFiscalBook, self)._get_options(previous_options)
		options.update({
			'book_type': 'purchase',
			'type': ['in_invoice', 'in_refund'],
			'move_state': ['posted'],
			'strings': {
				'resume_type': _('Compras'),
				'resume_tax': _('Crédito')
			},
		})
		return options

	def _get_columns_header(self):
		header = super(AccountPurchaseFiscalBook, self)._get_columns_header()
		header[11:11] = [
			{'field': 'nro_planilla_impor', 'name': _('N° de Planilla de Importación'), 'class': TEXT},
			{'field': 'import_file_number', 'name': _('N° de Expediente de Importación'), 'class': TEXT},
		]
		return header

	def _get_columns_tax_groups(self):
		tax_groups = super(AccountPurchaseFiscalBook, self)._get_columns_tax_groups()
		tax_groups[12:12] = [
			{'field': 'import_tax_base_general', 'name': _('Base Imponible Alícuota General'), 'class': NUMBER, 'type': 'base', 'group': 'import_general'},
			{'field': 'import_tax_percent_general', 'name': _('% Alícuota General'), 'class': TEXT, 'type': '', 'group': 'import_general'},
			{'field': 'import_tax_balance_general', 'name': _('Impuesto (I.V.A) Alícuota General'), 'class': NUMBER, 'type': 'tax', 'group': 'import_general'},
			{'field': 'import_tax_base_reduced', 'name': _('Base Imponible Alícuota Reducida'), 'class': NUMBER, 'type': 'base', 'group': 'import_reduced'},
			{'field': 'import_tax_percent_reduced', 'name': _('% Alícuota Reducida'), 'class': TEXT, 'type': '', 'group': 'import_reduced'},
			{'field': 'import_tax_balance_reduced', 'name': _('Impuesto (I.V.A) Alícuota Reducida'), 'class': NUMBER, 'type': 'tax', 'group': 'import_reduced'},
			{'field': 'import_tax_base_additional', 'name': _('Base Imponible Alícuota Adicional'), 'class': NUMBER, 'type': 'base', 'group': 'import_additional'},
			{'field': 'import_tax_percent_additional', 'name': _('% Alícuota Adicional'), 'class': TEXT, 'type': '', 'group': 'import_additional'},
			{'field': 'import_tax_balance_additional', 'name': _('Impuesto (I.V.A) Alícuota Adicional'), 'class': NUMBER, 'type': 'tax', 'group': 'import_additional'},
		]
		tax_groups.append({'field': 'wh_iva_withholding_rate', 'name': _('% de Retención'), 'class': TEXT, 'type': '', 'group': 'account_wh_iva'})
		return tax_groups