# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    #Pestana de documentos
    use_letter = fields.Binary(string="Carta de buen uso", attachment=True, required= True, copy=False)
    bank_transfer_receipt = fields.Binary(string="Comprobante de Transferencia", attachment=True, copy=False)
    contract = fields.Binary(string="Contrato", attachment=True, copy=False)
    foreign_currency_payroll = fields.Binary(string="Planilla de Recaudación Moneda Extranjera", attachment=True, copy=False)
    fund_availability = fields.Binary(string="Disponibilidad de Fondos", attachment=True, copy=False)
    release_authorization = fields.Binary(string="Autorización de la Exoneración", attachment=True, copy=False)
    sales_operational_worksheet = fields.Binary(string="Planilla de Operativo de Venta", attachment=True, copy=False)
    warehouse_domain = fields.Many2many('stock.warehouse')

    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén',
        default=False, domain="[('id', 'in', warehouse_domain)]")

    currency_selection = fields.Selection(
    [('0', 'Bolívares'),
    ('1', 'Divisas'),
    ('2', 'No Aplica')
    ], string="Moneda", copy=False)

    bolivar_payment = fields.Selection([
        ('0', 'Transferencia Bolívares'),
        ('1', 'Débito en Cuenta'),
    ], string="Forma de Pago (Bolívares)", copy=False)

    dollar_payment = fields.Selection([
        ('0', 'Divisas en Taquilla'),
        ('1', 'Transferencia Divisas'),
    ], string="Forma de Pago (Divisas)", copy=False)

    not_apply = fields.Selection([
        ('0', 'Exonerado'),
    ], string="Forma de Pago (No Aplica)", copy=False)

    #General pedido de venta
    finance_approved_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
    approved_regional_management_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
    approved_regional_management_user = fields.Many2one(comodel_name ='res.users', string='Aprobado por', copy=False)
    finance_approved_user = fields.Many2one(comodel_name ='res.users', string='Aprobado por', copy=False)

    order_ids = fields.One2many('sale.order', 'opportunity_id', related="opportunity_id.order_ids")

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('reg_manag', 'Espera de aprobación Gerencia Regional'),
        ('fin_approve', 'Espera de aprobación de Finanzas'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=False, copy=False, index=True, tracking=3, default='draft')
    appointment_date = fields.Date(string="Fecha de cita")
    sales_executive = fields.Many2one(comodel_name='res.users',string="Ejecutivo vendedor")

    #Campos traidos del modulo contactos
    affiliated = fields.Char(string="Numero de afiliación")
    denomination = fields.Char(string="Denominación comercial")
    cluster_id = fields.Many2one(comodel_name ='segmentation.cluster', string='Cluster', ondelete="restrict")
    name_owner =fields.Char(string ="Nombre y Apellido del Propietario")
    region_id = fields.Many2one('crm.region',string='Región', ondelete="restrict")
    phone_one = fields.Char(string="Teléfono")
    phone_two = fields.Char(string="Teléfono 2")
    phone_three = fields.Char(string="Teléfono 3")
    regional_manager = fields.Many2one(comodel_name='res.users', string="Gerente Regional")
    bank_ids = fields.One2many(related='partner_id.bank_ids', string='Banks')
    parent_id = fields.Many2one('res.partner', string='Empresa relacionada')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


    #Campos traidos del modulo CRM
    type_negotiation_id = fields.Many2one(comodel_name='crm.negotiation', string="Tipo de negociación", ondelete="restrict")
    product_type = fields.Selection([
        ('1', 'POS'),
        ('2', 'Accesorios'),
        ('3', 'POS y Accesorios')
    ], string="Tipo de Producto")
    type_point_sale_id = fields.Many2one(comodel_name='crm.point.sale', string="Tipo de comunicación", ondelete="restrict")
    company_pos_id = fields.Many2one(comodel_name='crm.company.pos', string="Operadora Telefónica", ondelete="restrict")
    origin_id = fields.Many2one(comodel_name='crm.origin', string="Origen", ondelete="restrict")
    kind_attention = fields.Selection([('1', 'Tradicional'), ('2', 'Evento'), ('3', 'VIP')], string="Tipo de atención", ondelete="restrict")
    event_name_id = fields.Many2one(comodel_name='event.name', string="Nombre del evento", ondelete="restrict")
    type_code = fields.Integer(related="type_point_sale_id.type_code")
    change_opportunity = fields.Boolean(compute='_compute_change_opportunity')
    inv = fields.Boolean(compute='_compute_inv')
    mail_partner_id = fields.Many2one('res.partner')

    def _compute_change_opportunity(self):
        if self.opportunity_id and self.state == 'sent' and len(self.opportunity_id.order_ids.filtered(lambda s: s.state == 'sent').ids) <= 1:
            self.change_opportunity = False
        else:
            self.change_opportunity = True

    #validaciones para el campo fecha de cita 
    @api.constrains('appointment_date')
    def _onchange_appointment_date(self):
        if self.appointment_date:
            if self.appointment_date < date.today():
                raise exceptions.ValidationError('La fecha de la cita no puede ser menor a la fecha actual')
            if self.opportunity_id.appointment_date != self.appointment_date:
                self.opportunity_id.appointment_date = self.appointment_date

    def write(self, values):
        state = self.state
        result = super(SaleOrder, self).write(values)
        if self.state not in ['cancel', 'sale', 'done'] and not self._context.get('no_validate_stock', False):
            self.restrict_sale_without_stock(state)
        if self.is_rental_order and any( line.product_template_id.product_type == '0' and not line.product_template_id.rent_ok for line in self.order_line):
            raise exceptions.ValidationError("No esta permitido vender productos de tipo \"POS\" a travez de un presupuesto de alquiler")
        return result

    #Carga de datos del cliente y validacion de cliente activo
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if ((self.partner_id.contact_type == '0' or self.partner_id.contact_type == '1') and self.partner_id.status_customer == '1') or not self.partner_id:
            self.denomination = self.partner_id.denomination
            self.cluster_id = self.partner_id.cluster_id
            self.name_owner = self.partner_id.name_owner
            self.region_id = self.partner_id.region_id
            self.phone_one = self.partner_id.phone_one
            self.phone_two = self.partner_id.phone_two
            self.phone_three = self.partner_id.phone_three
            self.regional_manager = self.partner_id.regional_manager
            self.user_id = self.partner_id.user_id
            self.sales_executive = self.partner_id.user_id
            self.affiliated = self.partner_id.affiliated
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2
            self.zip = self.partner_id.zip
            self.city = self.partner_id.city
            self.state_id = self.partner_id.state_id
            self.country_id = self.partner_id.country_id
            self.parent_id  = self.partner_id.parent_id
        else:
            raise exceptions.ValidationError('El contacto no esta habilitado para la creacion de un presupuesto')

    #carga de datos del CRM
    @api.onchange('opportunity_id')
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            self.type_negotiation_id = self.opportunity_id.type_negotiation_id
            self.product_type = self.opportunity_id.product_type
            self.type_point_sale_id = self.opportunity_id.type_point_sale_id
            self.company_pos_id = self.opportunity_id.company_pos_id
            self.origin_id = self.opportunity_id.origin_id
            self.kind_attention = self.opportunity_id.kind_attention
            self.event_name_id = self.opportunity_id.event_name_id
            self.appointment_date = self.opportunity_id.appointment_date 
            self.partner_invoice_id = self.opportunity_id.company_address
            self.origin = self.opportunity_id.lead_sequence
            self.set_domain()
    
    @api.constrains('opportunity_id')
    def set_budget_send(self):
        if not self.opportunity_id.budget_send and self.state == 'sent':
            self.opportunity_id.budget_send = True

    @api.onchange('origin')
    def _onchange_origin(self):
        if self.origin:
            opport = self.env['crm.lead'].search([('lead_sequence', '=', self.origin),('partner_id', '=', self.partner_id.id),('stage_code', '=', 3)], limit=1)
            if opport:
                if self.opportunity_id:
                    if self.opportunity_id.id != opport.id:
                        if opport.budget_send:
                            raise exceptions.ValidationError(_("You cannot assign sales quotes to opportunities with submitted quotes."))
                        else:
                            self.opportunity_id = opport
                elif opport.budget_send:
                    raise exceptions.ValidationError(_("You cannot assign sales quotes to opportunities with submitted quotes."))
                else:
                    self.opportunity_id = opport
            else:
                raise exceptions.ValidationError(_("No opportunity was found that matches the source document provided."))

    @api.onchange('kind_attention', 'event_name_id')
    def set_domain(self):
        if self.kind_attention == '2':
            self.warehouse_domain = self.env['stock.warehouse'].search([('kind_attention', '=', '2'), ('event', '=', self.event_name_id.id)])
        elif self.kind_attention in ['1', '3']:
            self.warehouse_domain = self.env['stock.warehouse'].search([('kind_attention', '=', '1')])
        
        if len(self.warehouse_domain) == 1:
            self.warehouse_id = self.warehouse_domain[0].id.origin
        else: 
            self.warehouse_id = False

    # direccion de factura debe ser igual en presupuestos y oportunidades
    @api.constrains('partner_invoice_id')
    def constrains_partner_invoice_id(self):
        if self.partner_invoice_id != self.opportunity_id.company_address:
            self.opportunity_id.company_address = self.partner_invoice_id

    #Buscar el contacto por el numero de afiliado
    @api.onchange('affiliated')
    def _onchange_affiliated(self):
        if self.affiliated:
            partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
            if partner:
                self.partner_id = partner.id
            else:
                raise exceptions.ValidationError('La afiliación ingresada no pertenece a ningun contacto')

    def action_quotation_send(self):
        self.restrict_sale_without_stock()
        return super(SaleOrder, self).action_quotation_send()

    #Extencion de funcion confirmar pedido de venta
    def action_confirm(self):
        if self.partner_id.status_customer == '1':
            if self.kind_attention != '2':
                self.opportunity_id.stage = self.env['crm.stage'].search([('stage_code', '=', 6)])
                self.opportunity_id.stage_code = 6
                self.opportunity_id.scheduled_date = True
            if not self.opportunity_id.budget_confirmed:
                self.opportunity_id.budget_confirmed = True
                self.opportunity_id.budget_confirmed_date = datetime.now()
            self.appointment_date = self.opportunity_id.appointment_date
            context = self._context
            self.finance_approved_user = context.get('uid')
            self.finance_approved_date = datetime.now()
            for order in self.opportunity_id.order_ids.filtered(lambda s: s.state in ['draft', 'sent', 'reg_manag', 'fin_approve'] and s.id != self.id):
                order.action_cancel()

            #send assigned to email
            lang = self.user_id.partner_id.lang if self.user_id.partner_id else None
            self.mail_partner_id = self.user_id.partner_id
            self.with_context(lang=lang)._message_auto_subscribe_notify([self.user_id.partner_id.id], 'sale_customization.message_sale_assigned')

            return super().action_confirm()
        else:
            raise exceptions.ValidationError('Cliente INACTIVO. No se puede confirmar el presupuesto')

    #Limpiar los campos al cambiar el tipo de moneda
    @api.onchange('currency_selection')
    def _onchange_currency_selection(self):
        self.bolivar_payment = False
        self.dollar_payment = False
        self.not_apply = False

    #Boton de aprobacion en estado de gerencia regional
    def approved_regional_management_button(self):
        context = self._context
        self.state = 'fin_approve'
        self.approved_regional_management_user = context.get('uid')
        self.approved_regional_management_date = datetime.now()
    
    asigned_partner = fields.Many2one('res.partner', copy=False)
    
    #cambio de chek presupuesto enviado en el CRM
    @api.constrains('state')
    def constrains_sent_invoice(self):
        if self.state == 'sent':
            if not self.opportunity_id.budget_send:
                self.opportunity_id.budget_send = True
                self.opportunity_id.budget_send_date = datetime.now()
        
        if self.state == 'fin_approve':
            if not self.asigned_partner:
                #get all users in the group
                partners = self.env['res.users'].search([]).filtered(lambda s: s.has_group("sale_customization.group_sale_finance_approval_notification")).partner_id
                if partners:
                    self.asigned_partner = partners.sorted(key = lambda s: s.asigned_orders)[0]
                    self.sudo().asigned_partner.asigned_orders +=1

                    if self.asigned_partner.asigned_orders == 2147480000:
                        for partner in partners:
                            partner.asigned_orders = 0
                
            if self.asigned_partner:
                if self.asigned_partner.id not in self.message_partner_ids.ids:
                    vals = {
                        'res_id': self.id,
                        'res_model': 'sale.order',
                        'partner_id': self.asigned_partner.id
                        }
                    self.env['mail.followers'].create(vals)
                lang = self.asigned_partner.lang if self.asigned_partner else None
                self.mail_partner_id = self.asigned_partner
                self.with_context(lang=lang)._message_auto_subscribe_notify([self.asigned_partner.id], 'sale_customization.message_sale_assigned')


    #Funcion de boton Solicitud de aprobación
    def approved_regional_management_change(self):
        cont = 0
        if self.partner_id.cedula == False or self.partner_id.rif == False:
            raise exceptions.ValidationError('El contacto no posee sus documentos completos')
        if self.opportunity_id:
            for record in self.opportunity_id.order_ids:
                if record.state == 'reg_manag' or record.state == 'fin_approve' or record.state == 'sale':
                    cont += 1
        if cont > 0:
            raise exceptions.ValidationError('Ya existe un presupuesto en espera de aprobación para esta oportunidad')
        else:
            self.opportunity_id.type_negotiation_id = self.type_negotiation_id
            self.opportunity_id.product_type = self.product_type
            self.opportunity_id.type_point_sale_id = self.type_point_sale_id 
            self.opportunity_id.company_pos_id = self.company_pos_id
            self.opportunity_id.origin_id = self.origin_id
            self.opportunity_id.kind_attention = self.kind_attention
            self.opportunity_id.event_name_id = self.event_name_id
            self.state = 'reg_manag'
        
        # add to followers
        if self.regional_manager.partner_id.id not in self.message_partner_ids.ids:
            vals = {
                'res_id': self.id,
                'res_model': 'sale.order',
                'partner_id': self.regional_manager.partner_id.id
                }
            self.env['mail.followers'].create(vals)

        # send approval notification
        self.send_approval_message(self.regional_manager)

        # self.env['mail.message'].create({
        #     'subject': _("Need approval"),
        #     'body': "<p>El pedido de venta necesita aprobación</p>",
        #     'model': 'sale.order',
        #     'res_id': self.id,
        #     'record_name': self.display_name,
        #     'message_type': 'notification',
        #     'partner_ids': [2, 3, 4],
        # })

    def send_approval_message(self, user):
        view = self.env['ir.ui.view'].browse(self.env['ir.model.data'].xmlid_to_res_id('sale_customization.message_sale_approval'))
        
        model_description = self.env['ir.model']._get(self._name).display_name
        values = {
            'object': self,
            'model_description': model_description,
        }
        assignation_msg = view.render(values, engine='ir.qweb', minimal_qcontext=True)
        assignation_msg = self.env['mail.thread']._replace_local_links(assignation_msg)
        self.message_notify(
            subject=_('Approval of %s') % self.display_name,
            body=assignation_msg,
            partner_ids=[user.partner_id.id],
            record_name=self.display_name,
            email_layout_xmlid='mail.mail_notification_light',
            model_description=model_description,
        )

    condition_create_invoice = fields.Boolean(default=True)
    @api.constrains('currency_selection', 'bolivar_payment', 'dollar_payment', 'not_apply', 'use_letter', 'bank_transfer_receipt', 'contract', 'foreign_currency_payroll', 'fund_availability', 'release_authorization', 'sales_operational_worksheet', 'appointment_date')
    def _onchange_condition_create_invoice(self):
        self.condition_create_invoice = True
        if self.kind_attention == '2':
            if self.currency_selection == '0' and self.bolivar_payment == '0' and self.bank_transfer_receipt and self.contract and self.use_letter and self.appointment_date:
                self.condition_create_invoice = False
            if self.currency_selection == '0' and self.bolivar_payment == '1' and self.fund_availability and self.contract  and self.use_letter and self.appointment_date:
                self.condition_create_invoice = False
            if self.currency_selection == '1' and self.dollar_payment == '0' and self.foreign_currency_payroll and self.contract and self.use_letter and self.appointment_date:
                self.condition_create_invoice = False
            if self.currency_selection == '1' and self.dollar_payment == '1' and self.bank_transfer_receipt and self.contract and self.use_letter and self.appointment_date:
                self.condition_create_invoice = False
            if self.currency_selection == '2' and self.not_apply == '0' and self.release_authorization and self.appointment_date:
                self.condition_create_invoice = False
        else:
            if self.currency_selection == '0' and self.bolivar_payment == '0' and self.bank_transfer_receipt and self.contract and self.use_letter:
                self.condition_create_invoice = False
            if self.currency_selection == '0' and self.bolivar_payment == '1' and self.fund_availability and self.contract  and self.use_letter:
                self.condition_create_invoice = False
            if self.currency_selection == '1' and self.dollar_payment == '0' and self.foreign_currency_payroll and self.contract and self.use_letter:
                self.condition_create_invoice = False
            if self.currency_selection == '1' and self.dollar_payment == '1' and self.bank_transfer_receipt and self.contract and self.use_letter:
                self.condition_create_invoice = False
            if self.currency_selection == '2' and self.not_apply == '0' and self.release_authorization:
                self.condition_create_invoice = False


    def _compute_condition_create_invoice_scheduled_date(self):
            if self.opportunity_id and self.kind_attention == '2' :
                if self.opportunity_id.scheduled_date or self.appointment_date:
                    self.create_invoice_scheduled_date = True
                else:
                    self.create_invoice_scheduled_date = False
            else:
                self.create_invoice_scheduled_date = True
    create_invoice_scheduled_date = fields.Boolean(compute=_compute_condition_create_invoice_scheduled_date)

    def no_approve(self):
        self.with_context(no_validate_stock = True).state = 'sent'
    
    def action_cancel(self):
        if self.state == 'sent' and self.opportunity_id and self.opportunity_id.stage_id.stage_code in [3, 4, 5] and not any(order.state == 'sale' for order in self.opportunity_id.order_ids):
            raise exceptions.ValidationError('No puede ser cancelado un presupuesto de venta si la oportunidad no posee un pedido de venta, si la oportunidad se encuentra en "En negociación", "En evaluación del cliente" o "En espera de cita"')
        else:
            super(SaleOrder, self).action_cancel()
    
    def action_draft(self):
        orders = self.with_context(no_validate_stock = True).filtered(lambda s: s.state in ['cancel', 'sent'])
        return orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
        })

    @api.depends('regional_manager')
    def _compute_inv(self):
        for rec in self:
            if rec.state == 'reg_manag' and rec.regional_manager:
                rec.inv = (rec.regional_manager.id != rec.env.user.id and not (rec.env.user.has_group('base.user_admin') or rec.env.user.has_group('sale_customization.group_sale_secundary_approver')))
            else:
                rec.inv = True

    def restrict_sale_without_stock(self, state=''):
        no_stock_product = {}
        actual_state = state if state != '' else self.state
        for line in self.order_line.filtered(lambda l: l.product_id.type == 'product'):
            if not line.is_rental and line.prod_qty_for_location < line.product_uom_qty:
                if no_stock_product.get(line.product_id, False):
                    no_stock_product[line.product_id][0] += int(line.product_uom_qty)
                else: 
                    no_stock_product[line.product_id] = [int(line.product_uom_qty), int(line.prod_qty_for_location)]

            if line.is_rental and actual_state=='draft' and line.prod_qty_for_location_rental < line.product_uom_qty:
                if no_stock_product.get(line.product_id, False):
                    no_stock_product[line.product_id][0] += int(line.product_uom_qty)
                else: 
                    no_stock_product[line.product_id] = [int(line.product_uom_qty), int(line.prod_qty_for_location_rental)]
        if no_stock_product:
            message = "No existen cantidades disponibles para los siguientes productos:\n"
            for product, counters in no_stock_product.items():
                message += "- {}. Necesario: {} Disponible: {} \n".format(product.name, counters[0], counters[1])
            raise exceptions.ValidationError(message)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    prod_qty_for_location = fields.Integer(compute='_compute_prod_qty_for_location')
    prod_qty_for_location_rental = fields.Integer(compute='_compute_prod_qty_for_location')

    @api.depends('product_id', 'product_uom_qty', 'qty_delivered', 'state', 'product_uom')
    def _compute_prod_qty_for_location(self):
        for rec in self:
            rec.prod_qty_for_location = 0
            rec.prod_qty_for_location_rental = 0
            if rec.order_id.warehouse_id and self.product_id:
                if rec.order_id.warehouse_id.sale_stock_location:
                    rec.prod_qty_for_location = rec.env['stock.quant']._get_available_quantity(rec.product_id, rec.order_id.warehouse_id.sale_stock_location)
                if rec.order_id.warehouse_id.rental_stock_location:
                    rec.prod_qty_for_location_rental = rec.env['stock.quant']._get_available_quantity(rec.product_id, rec.order_id.warehouse_id.rental_stock_location)
                

    @api.depends('product_id', 'product_uom_qty', 'qty_delivered', 'state', 'product_uom')
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if line.product_type == 'product' and line.product_uom and line.qty_to_deliver > 0:
                line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    product_uom_qty = fields.Float(digits='None Decimal')
    qty_delivered = fields.Float(digits='None Decimal')
    qty_invoiced = fields.Float(digits='None Decimal')