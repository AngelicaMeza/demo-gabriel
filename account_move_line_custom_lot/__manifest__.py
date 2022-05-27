# -*- coding: utf-8 -*-
{
	'name': "Facturación por lote",
	'summary': """Agregar lote asignado a los productos en lineas de factura de cliente""",
	'description': """
		Agregar los lotes seleccionados para cada producto en la salida
		de inventario en un presupuesto de venta, y al facturar dicho
		pedido lleva consigo los lotes a las lineas de factura
	""",
	'author': "ITSales",
	'website': "https://www.itsalescorp.com/",
	'category': 'Sales/Sales',
	'version': '0.1',
	'depends': ['base','account', 'sale'],
	'data': [
		'views/account_move_views.xml',
	],
}
