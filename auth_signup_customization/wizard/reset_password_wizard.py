# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResetPassword(models.TransientModel):
    _name = 'auth.signup.reset.password'
    _description = 'action to reset password of users'

    def do_send(self):
        active = self.env['res.users'].browse(self._context.get('active_ids', []))
        for record in active:
            if record.state == 'new':
                record.with_context(create_user=1).action_reset_password()
            else:
                record.action_reset_password()