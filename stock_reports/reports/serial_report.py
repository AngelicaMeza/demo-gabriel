from odoo import api, fields, models, _
import datetime

class ProductionLot(models.TransientModel):
	_name = 'stock.lot.report'
	
	def action_print_report(self):
		self = self.with_context(lang=self.env.user.lang)
		data = {'form': self._context.get('active_ids', [])}
		report = self.env.ref('stock_reports.serial_report_xlsx')
		action = report.report_action(self, data=data)
		return action

class MonthlyIncomeXSLXReport(models.AbstractModel):
	_name = 'report.stock_reports.serial_report'
	_inherit = 'report.report_xlsx.abstract'
	

	def _get_initial_data(self, domain):
		query = """
			SELECT
				lot.id, 
				lot.affiliated as affiliated,
				SUM(COALESCE(quant.quantity, 0.0)) as quantity,
				lot.terminal as terminal,
				pt.product_type as product_type,
				nego.name as negotiation,
				subs.code as sub_code,
				partner.name as sub_partner,
				pt.name as product_name,
				pt.default_code as internal_reference,
				warehouse.name as warehouse_name,
				locat.name as lot_location,
				company_pos.name as network_operator,
				sim_lot.name as sim,
				application_versions.name as application_version,
				cond.name as lot_condition,
				status.name as status,
				company.name as company,
				lot.note as description,
				lot.number_transactions,
				purchase_orders.name as purchase,
				sale_orders.name as sale

			FROM stock_production_lot as lot
				LEFT JOIN sale_subscription as subs on lot.subscription_id = subs.id
				LEFT JOIN crm_negotiation as nego on lot.negotiation_type_id = nego.id
				LEFT JOIN stock_quant as quant on quant.lot_id = lot.id and quant.quantity <> -1
				LEFT JOIN res_partner as partner on partner.id = subs.partner_id
				LEFT JOIN product_product as product on product.id = lot.product_id
				LEFT JOIN product_template as pt on pt.id = product.product_tmpl_id
				LEFT JOIN stock_warehouse as warehouse on warehouse.id = lot.warehouse_id
				LEFT JOIN stock_location as locat on locat.id = lot.current_location
				LEFT JOIN stock_production_lot as sim_lot on sim_lot.id = lot.sim_card
				LEFT JOIN product_product as sim_product on sim_product.id = sim_lot.product_id
				LEFT JOIN product_template as sim_pt on sim_pt.id = sim_product.product_tmpl_id 
				LEFT JOIN crm_company_pos as company_pos on company_pos.id = sim_pt.network_operator_id
				LEFT JOIN application_versions on application_versions.id = lot.application_version
				LEFT JOIN condition_stock as cond on cond.id = lot.condition_id
				LEFT JOIN status_stock as status on status.id = lot.status_id
				LEFT JOIN res_company as company on company.id = lot.company_id
				LEFT JOIN (SELECT purchase.name, move_line.lot_id FROM purchase_order as purchase
								JOIN purchase_order_line as purchase_line on purchase_line.order_id = purchase.id
								JOIN stock_move on stock_move.purchase_line_id = purchase_line.id
								JOIN stock_location as locat on locat.id = stock_move.location_id
								JOIN stock_move_line as move_line on move_line.move_id = stock_move.id
							WHERE 
								purchase.state in ('purchase', 'done')
								AND locat.usage = 'supplier'
						) as purchase_orders on purchase_orders.lot_id = lot.id
				LEFT JOIN (SELECT sale_order.name, move_line.lot_id FROM sale_order
								JOIN sale_order_line as sale_line on sale_line.order_id = sale_order.id
								JOIN stock_move on stock_move.sale_line_id = sale_line.id
								JOIN stock_location as locat on locat.id = stock_move.location_id
								JOIN stock_move_line as move_line on move_line.move_id = stock_move.id
							WHERE 
								sale_order.state in ('sale', 'done')
								AND locat.usage = 'customer'
						) as sale_orders on sale_orders.lot_id = lot.id

			GROUP BY lot.id, subs.code, partner.name, nego.name,
					pt.product_type, pt.name, pt.default_code, pt.default_code,
					warehouse.name, locat.name, company_pos.name, sim_lot.name,
					application_versions.name, cond.name, status.name, lot.note,
					lot.number_transactions, purchase_orders.name, sale_orders.name, company.name
			"""
		self._cr.execute(query)
		data = self.env.cr.dictfetchall()
		return data

	def _preprocess_initial_data(self, initial_data,domain):
		product_type = {'0': 'POS',
						'1': 'Router',
						'2': 'Accesorio',
						'3': 'Simcard',
						'4': 'Otro', 
						'5': 'Llave'}
		for data in initial_data:
			if data.get('sub_code', False) and data.get('sub_partner', False):
				data['subs'] = data['sub_code'] + ' - ' + data['sub_partner']
			data.pop('sub_code')
			data.pop('sub_partner')
			data.pop('id')
			if data['number_transactions'] == None:
				data['number_transactions'] = 0
			if data['product_type']:
				data['product_type'] = product_type.get(data['product_type'])

		return initial_data

	def write_headers(self, workbook, sheet,domain):
		columns = [
			'Número de afiliación',
			'Cantidades',
			'Terminal',
			'Tipo',
			'Tipo de negociación',
			'Suscripción',
			'Producto',
			'Referencia interna',
			'Almacén',
			'Ubicación',
			'Operadora',
			'SIM card',
			'Versión de aplicativo',
			'Condición',
			'Estatus',
			'Compañía',
			'Descripción',
			'Número de transacciones',
			'Pedido de compra',
			'Pedido de venta',
		]
		fmt_total_customer = workbook.add_format({
			'bold': True, 
			'bg_color': '#4ec6d3',
			'align': 'center',
			'valign': 'vcenter',
		})
		sheet.set_row(0, 30)
		max_len = 0
		for i, column in enumerate(columns):
			if len(column) > max_len:
				max_len = len(column)
		for i, column in enumerate(columns):
			if not len(column):
				sheet.set_column(i, i, max_len * 4)
			else:
				sheet.set_column(i, i, len(column) + 5)
			sheet.write(0, i, column, fmt_total_customer)

	def write_data(self, workbook, sheet, data):
		row_number = 1
		columns = {
			'affiliated':0,
			'quantity':1,
			'terminal':2,
			'product_type':3,
			'negotiation':4,
			'subs':5,
			'product_name':6,
			'internal_reference':7,
			'warehouse_name':8,
			'lot_location':9,
			'network_operator':10,
			'sim':11,
			'application_version':12,
			'lot_condition':13,
			'status':14,
			'company':15,
			'description':16,
			'number_transactions':17,
			'purchase':18,
			'sale':19,
		}
		for line in data:
			for field, i in columns.items():
				sheet.write_row(row_number, i, [line.get(field, '')])
			row_number += 1

	def generate_xlsx_report(self, workbook, data, objs):
		sheet = workbook.add_worksheet('Pestaña 1')
		self = self.with_context(lang=self.env.user.lang)
		# report values
		domain = data['form']
		initial_data = self._get_initial_data(domain)
		initial_data = self._preprocess_initial_data(initial_data,domain)
		self.write_headers(workbook,sheet,domain)
		self.write_data(workbook,sheet,initial_data)