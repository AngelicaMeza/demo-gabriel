# Copyright 2016 LasLabs Inc.
# Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>.
# Copyright 2018 Modoolar <info@modoolar.com>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging
import re
from datetime import datetime, timedelta

from odoo import _, api, fields, models

from ..exceptions import PassError

_logger = logging.getLogger(__name__)
try:
    import zxcvbn

    zxcvbn.feedback._ = _
except ImportError:
    _logger.debug(
        "Could not import zxcvbn. Please make sure this library is available"
        " in your environment."
    )


def delta_now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return fields.Datetime.to_string(dt)


class ResUsers(models.Model):
    _inherit = "res.users"

    password_write_date = fields.Datetime(
        "Last password update", readonly=True,
    )
    password_history_ids = fields.One2many(
        string="Password History",
        comodel_name="res.users.pass.history",
        inverse_name="user_id",
        readonly=True,
    )

    @api.model
    def create(self, vals):
        vals["password_write_date"] = fields.Datetime.now()
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        if vals.get("password"):
            self._check_password(vals["password"])
            vals["password_write_date"] = fields.Datetime.now()
        res =super(ResUsers, self).write(vals)
        if res and vals.get("password"):
            view = self.env['ir.ui.view'].browse(self.env['ir.model.data'].xmlid_to_res_id('password_security.password_change_message'))
        
            # model_description = self.env['ir.model']._get(self._name).display_name
            values = {
                'object': self,
                'model_description': '',
            }
            pw_change_msg = view.render(values, engine='ir.qweb', minimal_qcontext=True)
            pw_change_msg = self.env['mail.thread']._replace_local_links(pw_change_msg)
            self.env['mail.thread'].message_notify(
                subject=_('Password change'),
                body=pw_change_msg,
                partner_ids=[self.user_ids[0].partner_id.id],
                record_name=self.display_name,
                email_layout_xmlid='password_security.email_notification_light',
                model_description='',
            )
        return res

    @api.model
    def get_password_policy(self):
        data = super(ResUsers, self).get_password_policy()
        company_id = self.env.user.company_id
        data.update(
            {
                "password_lower": company_id.password_lower,
                "password_upper": company_id.password_upper,
                "password_numeric": company_id.password_numeric,
                "password_special": company_id.password_special,
                "password_length": company_id.password_length,
                "password_length_max": company_id.password_length_max,
                "password_estimate": company_id.password_estimate,
            }
        )
        return data

    def _check_password_policy(self, passwords):
        result = super(ResUsers, self)._check_password_policy(passwords)

        for password in passwords:
            if not password:
                continue
            self._check_password(password)

        return result

    @api.model
    def get_estimation(self, password):
        return zxcvbn.zxcvbn(password)

    def password_match_message(self):
        self.ensure_one()
        company_id = self.company_id
        message = []
        if company_id.password_lower:
            message.append(
                "\n* "
                + _("Letra minúscula (al menos ")
                + str(company_id.password_lower)
                + _(" Caracteres)")
            )
        if company_id.password_upper:
            message.append(
                "\n* "
                + _("Letra mayúscula (al menos ")
                + str(company_id.password_upper)
                + _(" Caracteres)")
            )
        if company_id.password_numeric:
            message.append(
                "\n* "
                + _("Dígito numérico (al menos ")
                + str(company_id.password_numeric)
                + _(" Caracteres)")
            )
        if company_id.password_special:
            message.append(
                "\n* "
                + _("Carácter especial (al menos ")
                + str(company_id.password_special)
                + _(" Caracteres)")
            )
        if message:
            message = [_("Must contain the following:")] + message
        if company_id.password_length_max <= 0:
            if company_id.password_length:
                message = [
                    _("La contraseña debe tener %d caracteres o más.") % company_id.password_length
                ] + message
        else:
            if company_id.password_length:
                message = [
                    _("la contraseña debe tener entre %d y %d caracteres.") % (company_id.password_length, company_id.password_length_max)
                ] + message
        message = message + [
            _("*La contraseña no puede tener 3 caracteres repetidos sucesivamente")
        ]
        return "\r".join(message)

    def _check_password(self, password):
        self._check_password_rules(password)
        self._check_password_history(password)
        return True

    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True
        company_id = self.company_id
        password_regex = [
            "^",
            "(?=.*?[a-z]){" + str(company_id.password_lower) + ",}",
            "(?=.*?[A-Z]){" + str(company_id.password_upper) + ",}",
            "(?=.*?\\d){" + str(company_id.password_numeric) + ",}",
            r"(?=.*?[\W_]){" + str(company_id.password_special) + ",}",
        ]
        if company_id.password_length_max > 0:
            password_regex.append(".{%d,%d}$" % (int(company_id.password_length), int(company_id.password_length_max)))
        else:
            password_regex.append(".{%d,}$" % int(company_id.password_length))

        if not re.search("".join(password_regex), password) or re.search(r'(.)\1\1', password):
            raise PassError(self.password_match_message())

        estimation = self.get_estimation(password)
        if estimation["score"] < company_id.password_estimate:
            raise PassError(estimation["feedback"]["warning"])

        return True

    def _password_has_expired(self):
        self.ensure_one()
        if not self.password_write_date:
            return True

        if not self.company_id.password_expiration:
            return False

        days = (fields.Datetime.now() - self.password_write_date).days
        return days > self.company_id.password_expiration

    def action_expire_password(self):
        expiration = delta_now(days=+1)
        for rec_id in self:
            rec_id.mapped("partner_id").signup_prepare(
                signup_type="reset", expiration=expiration
            )

    def _validate_pass_reset(self):
        """It provides validations before initiating a pass reset email
        :raises: PassError on invalidated pass reset attempt
        :return: True on allowed reset
        """
        for rec_id in self:
            pass_min = rec_id.company_id.password_minimum
            if pass_min <= 0:
                pass
            write_date = rec_id.password_write_date
            delta = timedelta(hours=pass_min)
            if write_date + delta > datetime.now():
                raise PassError(
                    _(
                        "Passwords can only be reset every %d hour(s). "
                        "Please contact an administrator for assistance."
                    )
                    % pass_min,
                )
        return True

    def _check_password_history(self, password):
        """It validates proposed password against existing history
        :raises: PassError on reused password
        """
        crypt = self._crypt_context()
        for rec_id in self:
            recent_passes = rec_id.company_id.password_history
            if recent_passes < 0:
                recent_passes = rec_id.password_history_ids
            else:
                recent_passes = rec_id.password_history_ids[0 : recent_passes - 1]
            if recent_passes.filtered(
                lambda r: crypt.verify(password, r.password_crypt)
            ):
                raise PassError(
                    _("Cannot use the most recent %d passwords")
                    % rec_id.company_id.password_history
                )

    def _set_encrypted_password(self, uid, pw):
        """ It saves password crypt history for history rules """
        super(ResUsers, self)._set_encrypted_password(uid, pw)

        self.write({"password_history_ids": [(0, 0, {"password_crypt": pw})]})
