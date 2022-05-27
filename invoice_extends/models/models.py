# -*- coding: utf-8 -*-

from odoo import models, fields, api
from num2words import lang_ES_VE, num2words
import re
import string


class invoice_extends(models.Model):
    _inherit="account.move"

    son = fields.Char(compute="compute_numbers_to_words")

    # transformacion de cantidades en numeros a palabras
    def compute_numbers_to_words(self):
        # conversion
        for rec in self:
            converted_amount = round(rec.currency_id._convert(rec.amount_total, rec.company_currency_id, rec.company_id, rec.date), 2)
            amount_txt = num2words(converted_amount, lang='es_VE', to="currency")
        
            # arreglos en el string resultado por cambios en la nomenclatura
            
            # cambio a monedas actuales actual:(fuertes -> soberanos) futuro:(fuertes/soberanos -> digitales)
            if rec.company_currency_id.name == "VES" and rec.company_currency_id.symbol == "Bs." and rec.company_currency_id.id == 3:
                if amount_txt.find("fuertes") != -1:
                    amount_txt = amount_txt.replace("fuertes", "digitales")
                    monetary_name = "digitales"
                else:
                    amount_txt = amount_txt.replace("un bolívar", "un bolívar digital")
                    monetary_name= "digital"
            # "de" despues de un numero redondo de millon o millones    
            if "millones" in amount_txt[len(amount_txt)-27:] or "millón" in amount_txt[len(amount_txt)-27:]:
                amount_txt = amount_txt[:len(amount_txt)-17] + "de " + amount_txt[len(amount_txt)-17:]
            
            # representacion de los centimos
            if amount_txt.find('centavos') != -1:
                amount_txt = amount_txt.replace("centavos", "centimos")
                y_position = amount_txt.find(monetary_name)+len(monetary_name)+1
                amount_txt = amount_txt[:y_position] + "con" + amount_txt[y_position+1:]
            else:
                amount_txt = amount_txt + " con cero centimos" if amount_txt else amount_txt
            
            amount_txt = amount_txt.title()
            
            rec.son = amount_txt.replace("Y", "y")
        
    def get_number(self, name):
        n = re.findall('.*/.*/([0-9]*)', name)
        if n:
            return n[0]
        else:
            return name