# coding: utf-8
###########################################################################

from odoo import models, fields, api, exceptions, _

class TxtIva(models.Model):
    _inherit = "txt.iva"

    def action_generate_lines_txt(self):
        """ Current lines are cleaned and rebuilt
        """
        rp_obj = self.env['res.partner']
        voucher_obj = self.env['account.wh.iva']
        txt_iva_obj = self.env['txt.iva.line']
        vouchers = []
        txt_brw = self.browse(self.ids)
        txt_ids = txt_iva_obj.search([('txt_id', '=', txt_brw.id)])
        if txt_ids:
            for txt in txt_ids: txt.unlink()

        if txt_brw.type:
            vouchers = voucher_obj.search([
                ('date_ret', '>=', txt_brw.date_start),
                ('date_ret', '<=', txt_brw.date_end),
                ('state', '=', 'done'),
                ('type', 'in', ['in_invoice', 'in_refund'])])
        else:
            vouchers = voucher_obj.search([
                ('date_ret', '>=', txt_brw.date_start),
                ('date_ret', '<=', txt_brw.date_end),
                ('state', '=', 'done'),
                ('type', 'in', ['out_invoice', 'out_refund'])])
        amount_total =0
        base_total = 0
        amount_exento = 0
        amount = 0
        base = 0
        for voucher in vouchers:

            acc_part_id = rp_obj._find_accounting_partner(voucher.partner_id)
            for voucher_lines in voucher.wh_lines:
                for voucher_tax_line in voucher_lines.tax_line:
                    ###################################################
                    if voucher_lines.invoice_id.type in ['out_refund', 'in_refund']:
                        amount_total -= voucher_tax_line.amount_ret
                        base_total -= voucher_tax_line.base
                    else:
                        amount_total += voucher_tax_line.amount_ret
                        base_total += voucher_tax_line.base
                    amount = voucher_tax_line.amount_ret
                    base = voucher_tax_line.base
                    ####################################################
                    if voucher_tax_line.wh_vat_line_id.invoice_id.type == 'in_invoice' or voucher_tax_line.wh_vat_line_id.invoice_id.type == 'in_refund':
                        type = 'purchase'
                    else:
                        type = 'sale'
                    busq = self.env['account.tax'].search([('id','=', voucher_tax_line.id_tax),('type_tax_use','=', type)])
                    if voucher_tax_line.amount == 0 and voucher_tax_line.amount_ret == 0:
                        amount_exento = voucher_tax_line.base

                    txt_iva_obj.create(
                        {'partner_id': acc_part_id.id,
                        'voucher_id': voucher.id,
                        'invoice_id': voucher_lines.invoice_id.id,
                        'txt_id': txt_brw.id,
                        # 'untaxed': voucher_tax_line.base,
                        'untaxed': base,#voucher_lines.base_ret,
                        'amount_withheld': amount,#voucher_lines.amount_tax_ret,
                        'amount_sdcf': amount_exento,  # self.get_amount_scdf(voucher_lines),
                        'tax_wh_iva_id': busq.name if busq else '',
                        })
                    busq = {}
                self.update({'amount_total_ret': amount_total,
                            'amount_total_base': base_total})
                if voucher_lines.invoice_id.state not in ['posted']:
                    pass
        return True

    def generate_txt(self):
        """ Return string with data of the current document
        """
        txt_string = ''
        final_amount_withheld = 0
        final_amount_untaxed = 0
        for txt in self:
            expediente = '0'
            for txt_line in txt.txt_ids:
                print("txt.txt_ids:  ",txt.txt_ids)
                vendor, buyer = self.get_buyer_vendor(txt, txt_line)
                if txt_line.invoice_id.type in ['out_invoice','out_refund']:
                    if vendor:
                        vendor = vendor.replace("-", "")
                    else:
                        vendor = ''
                    if buyer:
                        buyer = buyer.replace("-", "")
                    else:
                        buyer = ''
                else:
                    if buyer:
                        buyer = buyer.replace("-", "")
                    else:
                        buyer = ' '
                    if txt_line.partner_id.company_type == 'person':
                        if vendor:
                            vendor = vendor.replace("-", "")
                    else:
                        if vendor:
                            vendor = vendor.replace("-", "")
                        else:
                            vendor = ''
                period = self.get_period(txt.date_start)
                operation_type = ('V' if txt_line.invoice_id.type in ['out_invoice', 'out_refund'] else 'C')
                document_type = self.get_type_document(txt_line)
                document_number = self.get_document_number(txt_line, 'inv_number')
                control_number = self.get_number(txt_line.invoice_id.nro_ctrl, 'inv_ctrl', 20)
                document_affected = self.get_document_affected(txt_line)
                document_affected = document_affected.replace("-","") if document_affected else '0'
                voucher_number = self.get_number(txt_line.voucher_id.number, 'vou_number', 14)
                amount_exempt, amount_untaxed = self.get_amount_exempt_document(txt_line)
                alicuota = float(self.get_alicuota(txt_line))
                amount_total, amount_exempt = self.get_amount_line(txt_line, amount_exempt,alicuota)
                amount_exempt2 = str(round(txt_line.amount_sdcf, 2))
                if  document_type == '03':
                    ##########################################################################################################################################
                    document_affected = str(txt_line.invoice_id.reversed_entry_id.supplier_invoice_number or txt_line.invoice_id.credit_note_number)
                    ##########################################################################################################################################
                if txt_line.voucher_id == txt_line.invoice_id.wh_iva_id:
                    amount_untaxed = txt_line.untaxed
                else:
                    amount_untaxed = amount_untaxed
                txt_line.untaxed2 = str(round(txt_line.untaxed, 2))
                txt_line.amount_withheld2 = str(round(txt_line.amount_withheld, 2))
                if float(txt_line.amount_withheld2) < 0 :
                    final_amount_withheld = float(txt_line.amount_withheld2) * -1
                else:
                    final_amount_withheld = float(txt_line.amount_withheld2)
                if float(amount_untaxed) < 0:
                    final_amount_untaxed = float(amount_untaxed) * -1
                else:
                    final_amount_untaxed = float(amount_untaxed)
                if document_type == '05':
                    expediente = str(txt_line.invoice_id.nro_expediente_impor)
                txt_string = (
                    txt_string + buyer + '\t' + period + '\t'
                    + (str(txt_line.invoice_id.invoice_date)) + '\t' + operation_type +
                    '\t' + document_type + '\t' + vendor + '\t' +
                    document_number + '\t' + control_number + '\t' +
                    str(f"{'{:.2f}'.format(amount_total)}")+ '\t' +
                    self.formato_cifras(final_amount_untaxed) + '\t' +
                    self.formato_cifras(final_amount_withheld) + '\t' + document_affected + '\t' + voucher_number
                    + '\t' + self.formato_cifras(amount_exempt2) + '\t' + self.formato_cifras(alicuota)
                    + '\t' + expediente + '\n')
        return txt_string