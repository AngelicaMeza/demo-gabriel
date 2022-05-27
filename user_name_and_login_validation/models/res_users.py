# -*- coding: utf-8 -*-

from odoo import exceptions, models, fields, api, _
import re

class Users(models.Model):
    _inherit = "res.users"

    @api.constrains('name')
    def no_special_characters(self):
        if self.name:
            if re.search("[^a-zA-z\sáéíóúüÁÉÍÓÚÜñÑ]", self.name):
                raise exceptions.ValidationError(_("The user name can't have spacial charecters"))
            elif re.search(r'(\s)\1', self.name) or len(self.name) < 6:
                raise exceptions.ValidationError(_("The user name must be single-spaced and at least 6 characters long"))

    @api.constrains('login')
    def validate_email_addrs(self):
        # mail_obj = re.compile(r"""
        #         \b              # comienzo de delimitador de palabra
        #         [\w._]        # usuario: Cualquier caracter alfanumerico mas los signos (.%+-)
        #         +@              # seguido de @
        #         [\w.-]          # dominio: Cualquier caracter alfanumerico mas los signos (.-)
        #         +\.             # seguido de .
        #         [a-zA-Z]{2,3}   # dominio de alto nivel: 2 a 6 letras en minúsculas o mayúsculas.
        #         \b              # fin de delimitador de palabra
        #         """, re.X)      # bandera de compilacion X: habilita la modo verborrágico, el cual permite organizar
        #                         # el patrón de búsqueda de una forma que sea más sencilla de entender y leer.
        # if not mail_obj.search(self.login):
            
        if not re.match('^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}$',self.login):
            raise exceptions.ValidationError(_("The mailing address must comply with the following format: jsmith@example.com"))

        self.no_special_characters()

        self.partner_id.email = self.login

    @api.model
    def create(self, vals):
        res = super(Users, self).create(vals)
        self.env.user.notify_success(message=_("The user was created successfully"), title=_("success"))
        return res