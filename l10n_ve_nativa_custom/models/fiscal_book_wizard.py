# coding: utf-8

import math

from odoo import fields, models, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class PurchaseBook(models.AbstractModel):

    _inherit = 'report.l10n_ve_fiscal_book.report_fiscal_purchase_book'

    @api.model
    def _get_report_values(self, docids, data=None):
        format_new = "%d/%m/%Y"
        date_start = datetime.strptime(data['form']['date_from'], DATE_FORMAT)
        date_end = datetime.strptime(data['form']['date_to'], DATE_FORMAT)
        datos_compras = []
        purchasebook_ids = self.env['fiscal.book.line'].search(
            [('fb_id', '=', data['form']['book_id']), ('accounting_date', '>=', date_start.strftime(DATETIME_FORMAT)), ('accounting_date', '<=', date_end.strftime(DATETIME_FORMAT))])
        emission_date = ' '
        sum_compras_credit = 0
        sum_total_with_iva = 0
        sum_vat_general_base = 0
        sum_vat_general_tax = 0
        sum_vat_reduced_base = 0
        sum_vat_reduced_tax = 0
        sum_vat_additional_base = 0
        sum_vat_additional_tax = 0
        sum_get_wh_vat = 0
        suma_vat_exempt = 0

        vat_reduced_base = 0
        vat_reduced_rate = 0
        vat_reduced_tax = 0
        vat_additional_base = 0
        vat_additional_rate = 0
        vat_additional_tax = 0

        ''' COMPRAS DE IMPORTACIONES'''

        sum_total_with_iva_importaciones = 0
        sum_vat_general_base_importaciones = 0
        suma_base_general_importaciones = 0
        sum_base_general_tax_importaciones = 0
        sum_vat_general_tax_importaciones = 0
        sum_vat_reduced_base_importaciones = 0
        sum_vat_reduced_tax_importaciones = 0
        sum_vat_additional_base_importaciones = 0
        sum_vat_additional_tax_importaciones = 0

        hola = 0
        #######################################
        compras_credit = 0
        origin = 0
        number = 0

        for h in purchasebook_ids:
            h_vat_general_base = 0.0
            h_vat_general_rate = 0.0
            h_vat_general_tax = 0.0
            vat_general_base_importaciones = 0
            vat_general_rate_importaciones = 0
            vat_general_general_rate_importaciones = 0
            vat_general_tax_importaciones = 0
            vat_reduced_base_importaciones = 0
            vat_reduced_rate_importaciones = 0
            vat_reduced_tax_importaciones = 0
            vat_additional_tax_importaciones = 0
            vat_additional_rate_importaciones = 0
            vat_additional_base_importaciones = 0
            vat_reduced_base = 0
            vat_reduced_rate = 0
            vat_reduced_tax = 0
            vat_additional_base = 0
            vat_additional_rate = 0
            vat_additional_tax = 0
            get_wh_vat = 0

            if h.type == 'ntp':
                compras_credit = h.invoice_id.amount_untaxed

            if h.doc_type == 'N/C':
                origin = h.affected_invoice
                if h.invoice_id:
                    if h.invoice_id.nro_ctrl:
                        busq1 = self.env['account.move'].search(
                            [('nro_ctrl', '=', h.invoice_id.nro_ctrl)])
                        if busq1:
                            for busq2 in busq1:
                                if busq2.type == 'in_invoice':
                                    number = busq2.name or ''

            sum_compras_credit += compras_credit
            if h.doc_type == 'N/C':

                suma_vat_exempt -= h.vat_exempt
            else:
                suma_vat_exempt += h.vat_exempt
            planilla = ''
            expediente = ''
            total = 0
            h.total_with_iva = 0

            partner = self.env['res.partner'].search(
                [('name', '=', h.partner_name)])

            if len(partner) > 1:
                if h.invoice_id:
                    partner = h.invoice_id.partner_id
                    partner_ret = h.invoice_id.partner_id.wh_iva_rate
                elif h.iwdl_id:
                    partner = h.iwdl_id.invoice_id.partner_id
                    partner_ret = h.iwdl_id.invoice_id.partner_id.wh_iva_rate
            if h.invoice_id:
                partner = h.invoice_id.partner_id
                partner_ret = h.invoice_id.partner_id.wh_iva_rate
            elif h.iwdl_id:

                partner_ret = h.iwdl_id.invoice_id.partner_id.wh_iva_rate

                # partner = partner[0]
            if (partner.company_type == 'company' or partner.company_type == 'person') and (partner.people_type_company or partner.people_type_individual) and (partner.people_type_company == 'pjdo' or partner.people_type_individual == 'pnre' or partner.people_type_individual == 'pnnr'):
                '####################### NO ES PROVEDOR INTERNACIONAL########################################################3'

                if h.invoice_id:

                    # if h.doc_type == 'N/C':
                    #     total = h.invoice_id.currency_id._convert((h.invoice_id.amount_total * -1), h.invoice_id.company_currency_id, h.invoice_id.company_id, h.invoice_id.date)
                    #else:
                    total = h.invoice_id.currency_id._convert(
                        h.invoice_id.amount_total, h.invoice_id.company_currency_id, h.invoice_id.company_id, h.invoice_id.date)

                    if h.doc_type == 'N/C':
                        # IMPUESTO DE IVA ALICUOTA ADICIONAL
                        sum_vat_additional_tax -= h.vat_additional_tax
                        sum_total_with_iva -= total  # Total monto con IVA
                        sum_vat_general_base -= h.vat_general_base  # Base Imponible Alicuota general
                        sum_vat_general_tax -= h.vat_general_tax
                        # Base Imponible de alicuota Reducida
                        sum_vat_reduced_base -= h.vat_reduced_base
                        sum_vat_reduced_tax -= h.vat_reduced_tax  # Impuesto de IVA alicuota reducida
                        # BASE IMPONIBLE ALICUOTA ADICIONAL
                        sum_vat_additional_base -= h.vat_additional_base
                    else:
                        # IMPUESTO DE IVA ALICUOTA ADICIONAL
                        sum_vat_additional_tax += h.vat_additional_tax
                        # Base Imponible de alicuota Reducida
                        sum_vat_reduced_base += h.vat_reduced_base
                        sum_vat_reduced_tax += h.vat_reduced_tax  # Impuesto de IVA alicuota reducida
                        # BASE IMPONIBLE ALICUOTA ADICIONAL
                        sum_vat_additional_base += h.vat_additional_base
                        sum_total_with_iva += total
                        sum_vat_general_base += h.vat_general_base  # Base Imponible Alicuota general
                        sum_vat_general_tax += h.vat_general_tax
                     # Total monto con IVA

                    h_vat_general_base = h.vat_general_base
                    tax_base = 0
                    for iva in h.fbt_ids:
                        tax_base += iva.tax_amount
                    if tax_base > 0:
                        h_vat_general_rate = '16'

                    # if h.fbt_ids[0].name[5:7] != '16':
                    #     h_vat_general_rate = '0'
                    # else:
                    #     h_vat_general_rate =h.fbt_ids[0].name[5:7] if h.fbt_ids else False
                    h_vat_general_tax = h.vat_general_tax if h.vat_general_tax else 0.0
                    vat_reduced_base = h.vat_reduced_base
                    vat_reduced_rate = int(
                        h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                    vat_reduced_tax = h.vat_reduced_tax
                    vat_additional_base = h.vat_additional_base
                    vat_additional_rate = int(
                        h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                    vat_additional_tax = h.vat_additional_tax
                    get_wh_vat = h.get_wh_vat

                    emission_date = datetime.strftime(datetime.strptime(str(h.emission_date), DEFAULT_SERVER_DATE_FORMAT),
                                                       format_new)
                ##############################################
                elif h.iwdl_id.invoice_id:
                ##############################################

                    # if h.doc_type == 'N/C':
                    #     total = h.iwdl_id.invoice_id.currency_id._convert((h.iwdl_id.invoice_id.amount_total * -1), h.iwdl_id.invoice_id.company_currency_id, h.iwdl_id.invoice_id.company_id, h.iwdl_id.invoice_id.date)
                    #else:
                    total = h.iwdl_id.invoice_id.currency_id._convert(
                        h.iwdl_id.invoice_id.amount_total, h.iwdl_id.invoice_id.company_currency_id, h.iwdl_id.invoice_id.company_id, h.iwdl_id.invoice_id.date)

                    if h.doc_type == 'N/C':
                        sum_total_with_iva -= total  # Total monto con IVA
                        sum_vat_general_base -= h.vat_general_base  # Base Imponible Alicuota general
                        sum_vat_general_tax -= h.vat_general_tax  # Impuesto de IVA
                        # Base Imponible de alicuota Reducida
                        sum_vat_reduced_base -= h.vat_reduced_base
                        sum_vat_reduced_tax -= h.vat_reduced_tax
                    # Impuesto de IVA alicuota reducida
                        # BASE IMPONIBLE ALICUOTA ADICIONAL
                        sum_vat_additional_base -= h.vat_additional_base
                        # IMPUESTO DE IVA ALICUOTA ADICIONAL
                        sum_vat_additional_tax -= h.vat_additional_tax
                    else:
                        sum_total_with_iva += total
                        sum_vat_general_base += h.vat_general_base  # Base Imponible Alicuota general
                        sum_vat_general_tax += h.vat_general_tax  # Impuesto de IVA
                        # Base Imponible de alicuota Reducida
                        sum_vat_reduced_base += h.vat_reduced_base
                        sum_vat_reduced_tax += h.vat_reduced_tax
                    # Impuesto de IVA alicuota reducida
                        # BASE IMPONIBLE ALICUOTA ADICIONAL
                        sum_vat_additional_base += h.vat_additional_base
                        # IMPUESTO DE IVA ALICUOTA ADICIONAL
                        sum_vat_additional_tax += h.vat_additional_tax
                    # sum_vat_general_base += h.vat_general_base  # Base Imponible Alicuota general
                    # sum_vat_general_tax += h.vat_general_tax  # Impuesto de IVA
                    h_vat_general_base = h.vat_general_base

                    tax_base = 0
                    for iva in h.fbt_ids:
                        tax_base += iva.tax_amount

                    if tax_base > 0:
                        h_vat_general_rate = '16'
                    # if h.fbt_ids[0].name[5:7] != '16':
                    #     h_vat_general_rate = '0'
                    # else:
                    #     h_vat_general_rate =h.fbt_ids[0].name[5:7] if h.fbt_ids else False
                    h_vat_general_tax = h.vat_general_tax if h.vat_general_tax else 0.0
                    vat_reduced_base = h.vat_reduced_base
                    vat_reduced_rate = int(
                        h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                    vat_reduced_tax = h.vat_reduced_tax
                    vat_additional_base = h.vat_additional_base
                    vat_additional_rate = int(
                        h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                    vat_additional_tax = h.vat_additional_tax
                    get_wh_vat = h.get_wh_vat

                    emission_date = datetime.strftime(
                        datetime.strptime(str(h.emission_date),
                                          DEFAULT_SERVER_DATE_FORMAT),
                        format_new)

            if (partner.company_type == 'company' or partner.company_type == 'person') and (partner.people_type_company or partner.people_type_individual) and partner.people_type_company == 'pjnd':
                '############## ES UN PROVEEDOR INTERNACIONAL ##############################################'

                if h.invoice_id:
                    if h.invoice_id.fecha_importacion:
                        date_impor = h.invoice_id.fecha_importacion
                        emission_date = datetime.strftime(datetime.strptime(str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                                                       format_new)
                        total = h.invoice_id.amount_total
                    else:
                        date_impor = h.invoice_id.invoice_date
                        emission_date = datetime.strftime(
                            datetime.strptime(
                                str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                            format_new)

                    planilla = h.invoice_id.nro_planilla_impor
                    expediente = h.invoice_id.nro_expediente_impor
                else:
                    date_impor = h.iwdl_id.invoice_id.fecha_importacion
                    emission_date = datetime.strftime(datetime.strptime(str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                                                      format_new)
                    planilla = h.iwdl_id.invoice_id.nro_planilla_impor
                    expediente = h.iwdl_id.invoice_id.nro_expediente_impor
                    total = h.iwdl_id.invoice_id.amount_total
                get_wh_vat = 0.0
                vat_reduced_base = 0
                vat_reduced_rate = 0
                vat_reduced_tax = 0
                vat_additional_base = 0
                vat_additional_rate = 0
                vat_additional_tax = 0
                'ALICUOTA GENERAL IMPORTACIONES'
                vat_general_base_importaciones = h.vat_general_base
                vat_general_rate_importaciones = int(
                    h.vat_general_base and h.vat_general_tax * 100 / h.vat_general_base)
                vat_general_tax_importaciones = h.vat_general_tax
                'ALICUOTA REDUCIDA IMPORTACIONES'
                vat_reduced_base_importaciones = h.vat_reduced_base
                vat_reduced_rate_importaciones = int(
                    h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                vat_reduced_tax_importaciones = h.vat_reduced_tax
                'ALICUOTA ADICIONAL IMPORTACIONES'
                vat_additional_base_importaciones = h.vat_additional_base
                vat_additional_rate_importaciones = int(
                    h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                vat_additional_tax_importaciones = h.vat_additional_tax
                'Suma total compras con IVA'
                if h.doc_type == 'N/C':
                    sum_total_with_iva -= total  # Total monto con IVA
                    sum_vat_general_base_importaciones -= h.vat_general_base + \
                        h.vat_reduced_base + h.vat_additional_base  # Base Imponible Alicuota general
                    sum_vat_general_tax_importaciones -= h.vat_general_tax + \
                        h.vat_additional_tax + h.vat_reduced_tax  # Impuesto de IVA
                else:
                    sum_vat_general_base_importaciones += h.vat_general_base + \
                        h.vat_reduced_base + h.vat_additional_base  # Base Imponible Alicuota general
                    sum_vat_general_tax_importaciones += h.vat_general_tax + \
                        h.vat_additional_tax + h.vat_reduced_tax  # Impuesto de IVA
                    sum_total_with_iva += total
                 # Total monto con IVA
                'SUMA TOTAL DE TODAS LAS ALICUOTAS PARA LAS IMPORTACIONES'

                'Suma total de Alicuota General'
                suma_base_general_importaciones += h.vat_general_base
                sum_base_general_tax_importaciones += h.vat_general_tax

                ' Suma total de Alicuota Reducida'
                # Base Imponible de alicuota Reducida
                sum_vat_reduced_base_importaciones += h.vat_reduced_base
                # Impuesto de IVA alicuota reducida
                sum_vat_reduced_tax_importaciones += h.vat_reduced_tax
                'Suma total de Alicuota Adicional'
                # BASE IMPONIBLE ALICUOTA ADICIONAL
                sum_vat_additional_base_importaciones += h.vat_additional_base
                # IMPUESTO DE IVA ALICUOTA ADICIONAL
                sum_vat_additional_tax_importaciones += h.vat_additional_tax

                get_wh_vat = h.get_wh_vat

            if h.doc_type == 'N/C':
                sum_get_wh_vat -= h.get_wh_vat  # IVA RETENIDO
            else:
                sum_get_wh_vat += h.get_wh_vat  # IVA RETENIDO

            if h_vat_general_base != 0:
                valor_base_imponible = h.vat_general_base
                valor_alic_general = h_vat_general_rate
                valor_iva = h_vat_general_tax
            else:
                valor_base_imponible = 0
                valor_alic_general = 0
                valor_iva = 0

            if get_wh_vat != 0:
                hola = get_wh_vat
            else:
                hola = 0

            if h.vat_exempt != 0:
                vat_exempt = h.vat_exempt

            else:
                vat_exempt = 0

            'Para las diferentes alicuotas que pueda tener el proveedor  internacional'
            'todas son mayor a 0'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(vat_general_rate_importaciones) + ',' + ' ' + str(
                    vat_reduced_rate_importaciones) + ',' + ' ' + str(vat_additional_rate_importaciones) + ' '
            'todas son cero'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = 0
            'Existe reducida y adicional'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(
                    vat_reduced_rate_importaciones) + ',' + ' ' + str(vat_additional_rate_importaciones) + ' '
            'Existe general y adicional'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(
                    vat_general_rate_importaciones) + ',' + ' ' + str(vat_additional_rate_importaciones) + ' '
            'Existe general y reducida'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(
                    vat_general_rate_importaciones) + ',' + ' ' + str(vat_reduced_rate_importaciones) + ' '
            'Existe solo la general'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(
                    vat_general_rate_importaciones)
            'Existe solo la reducida'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(
                    vat_reduced_rate_importaciones)
            'Existe solo la adicional'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(
                    vat_additional_rate_importaciones)

            # if valor_alic_general == 0:
            #     total=0

            if h.invoice_id:
                supplier_numb_invoice = h.invoice_id.supplier_invoice_number
            else:
                supplier_numb_invoice = h.iwdl_id.supplier_invoice_number
            if h.debit_affected or h.credit_affected:
                supplier_numb_invoice = ""

            datos_compras.append({

                'emission_date': emission_date if emission_date else ' ',
                'partner_vat': h.partner_vat if h.partner_vat else ' ',
                'partner_name': h.partner_name,
                'people_type': h.people_type,
                'wh_number': h.wh_number if h.wh_number else ' ',
                'supplier_invoice_number': supplier_numb_invoice,
                'affected_invoice': h.affected_invoice,
                'ctrl_number': h.ctrl_number,
                'debit_affected':  h.credit_affected,
                'credit_affected': h.debit_affected,  # h.credit_affected,
                'type': self.get_t_type(doc_type=h.doc_type),
                'doc_type': h.doc_type,
                'origin': origin,
                'number': number,
                'total_with_iva': total,
                'vat_exempt': vat_exempt,
                'compras_credit': compras_credit,
                'vat_general_base': valor_base_imponible,
                'vat_general_rate': valor_alic_general,
                'vat_general_tax': valor_iva,
                'vat_reduced_base': vat_reduced_base,
                'vat_reduced_rate': vat_reduced_rate,
                'vat_reduced_tax': vat_reduced_tax,
                'vat_additional_base': vat_additional_base,
                'vat_additional_rate': vat_additional_rate,
                'vat_additional_tax':  vat_additional_tax,
                'get_wh_vat': hola,
                'vat_general_base_importaciones': vat_general_base_importaciones + vat_additional_base_importaciones + vat_reduced_base_importaciones,
                'vat_general_rate_importaciones': vat_general_general_rate_importaciones,
                'vat_general_tax_importaciones': vat_general_tax_importaciones + vat_reduced_tax_importaciones + vat_additional_tax_importaciones,
                'nro_planilla': planilla,
                'nro_expediente': expediente,
                'partner_ret': str(math.trunc(partner_ret))+"%"
            })
        'SUMA TOTAL DE ALICUOTA ADICIONAL BASE'
        if sum_vat_additional_base != 0 and sum_vat_additional_base_importaciones > 0:
            sum_ali_gene_addi = sum_vat_additional_base
            sum_vat_additional_base = sum_vat_additional_base
        else:
            sum_ali_gene_addi = sum_vat_additional_base
        'SUMA TOTAL DE ALICUOTA ADICIONAL TAX'
        if sum_vat_additional_tax != 0 and sum_vat_additional_tax_importaciones > 0:
            sum_ali_gene_addi_credit = sum_vat_additional_tax
            # sum_vat_additional_tax = sum_vat_additional_tax
        else:
            sum_ali_gene_addi_credit = sum_vat_additional_tax
        # 'SUMA TOTAL DE ALICUOTA GENERAL BASE'
        # if sum_vat_general_base != 0 and suma_base_general_importaciones > 0:
        #     sum_vat_general_base = sum_vat_general_base
        #     sum_vat_general_tax =  sum_vat_general_tax
        'SUMA TOTAL DE ALICUOTA REDUCIDA BASE'
        if sum_vat_reduced_base != 0 and sum_vat_reduced_base_importaciones > 0:
            sum_vat_reduced_base = sum_vat_reduced_base
            sum_vat_reduced_tax = sum_vat_reduced_tax

        ' IMPORTACIONES ALICUOTA GENERAL + ALICUOTA ADICIONAL'
        if sum_vat_additional_base_importaciones != 0:
            sum_ali_gene_addi_importaciones = sum_vat_additional_base_importaciones
        else:
            sum_ali_gene_addi_importaciones = sum_vat_additional_base_importaciones

        if sum_vat_additional_tax_importaciones != 0:
            sum_ali_gene_addi_credit_importaciones = sum_vat_additional_tax_importaciones
        else:
            sum_ali_gene_addi_credit_importaciones = sum_vat_additional_tax_importaciones

        total_compras_base_imponible = sum_vat_general_base + sum_ali_gene_addi + sum_vat_reduced_base + \
            suma_base_general_importaciones + sum_ali_gene_addi_importaciones + \
                sum_vat_reduced_base_importaciones + suma_vat_exempt
        total_compras_credit_fiscal = sum_vat_general_tax + sum_ali_gene_addi_credit + sum_vat_reduced_tax + \
            sum_base_general_tax_importaciones + \
                sum_ali_gene_addi_credit_importaciones + sum_vat_reduced_tax_importaciones

        date_start = datetime.strftime(datetime.strptime(
            data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT), format_new)
        date_end = datetime.strftime(datetime.strptime(
            data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT), format_new)

        if purchasebook_ids.env.company and purchasebook_ids.env.company.street:
            street = str(purchasebook_ids.env.company.street) + ','
        else:
            street = ' '
        datos_compras = sorted(datos_compras, key=lambda datos_compras: datetime.strptime(datos_compras['emission_date'], "%d/%m/%Y") ) 
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'a': 0.00,
            'street': street,
            'company': purchasebook_ids.env.company,
            'datos_compras': datos_compras,
            'sum_compras_credit': sum_compras_credit,
            'sum_total_with_iva': sum_total_with_iva,
            'suma_vat_exempt': suma_vat_exempt,
            'sum_vat_general_base': sum_vat_general_base,
            'sum_vat_general_tax': sum_vat_general_tax,
            'sum_vat_reduced_base': sum_vat_reduced_base,
            'sum_vat_reduced_tax': sum_vat_reduced_tax,
            'sum_vat_additional_base': sum_vat_additional_base,
            'sum_vat_additional_tax': sum_vat_additional_tax,
            'sum_get_wh_vat': sum_get_wh_vat,
            'sum_ali_gene_addi': sum_ali_gene_addi,
            'sum_ali_gene_addi_credit': sum_ali_gene_addi_credit,
            'suma_base_general_importaciones': suma_base_general_importaciones,
            'sum_base_general_tax_importaciones': sum_base_general_tax_importaciones,
            'sum_vat_general_base_importaciones': sum_vat_general_base_importaciones,
            'sum_vat_general_tax_importaciones': sum_vat_general_tax_importaciones,
            'sum_ali_gene_addi_importaciones': sum_ali_gene_addi_importaciones,
            'sum_ali_gene_addi_credit_importaciones': sum_ali_gene_addi_credit_importaciones,
            'sum_vat_reduced_base_importaciones': sum_vat_reduced_base_importaciones,
            'sum_vat_reduced_tax_importaciones': sum_vat_reduced_tax_importaciones,
            'total_compras_base_imponible': total_compras_base_imponible,
            'total_compras_credit_fiscal': total_compras_credit_fiscal,

        }
#