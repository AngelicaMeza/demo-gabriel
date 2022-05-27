# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import werkzeug
from odoo import SUPERUSER_ID, http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import Home
from odoo.addons.auth_signup.models.res_users import SignupError

_logger = logging.getLogger(__name__)

class AuthSignupHome(Home):

	@http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
	def web_auth_reset_password(self, *args, **kw):
		qcontext = self.get_auth_signup_qcontext()

		if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
			raise werkzeug.exceptions.NotFound()

		if 'error' not in qcontext and request.httprequest.method == 'POST':
			try:
				if qcontext.get('token'):
					self.do_signup(qcontext)
					return self.web_login(*args, **kw)
				else:
					login = qcontext.get('login')
					assert login, _("No login provided.")
					_logger.info("Password reset attempt for <%s> by user <%s> from %s", login, request.env.user.login, request.httprequest.remote_addr)
					request.env['res.users'].sudo().reset_password(login)
					qcontext['message'] = _("An email has been sent with credentials to reset your password")
			except UserError as e:
				qcontext['error'] = e.name or e.value
			except SignupError:
				qcontext['error'] = _("Could not reset your password")
				_logger.exception('error when resetting password')
			except Exception as e:
				qcontext['error'] = str(e)

		##############################################################################
		#CLEAN USER SESSION AND REDIRECT AGAIN TO RESET PASSWORD
		##############################################################################
		user = request.env['res.users'].with_user(SUPERUSER_ID).search(
			[('name', '=', qcontext.get('name')),
			('login', '=', qcontext.get('login'))
		])
		
		if user.logged_in and kw.get('db') and kw.get('token'):
			user.sudo()._clear_session()
			request.session.logout(keep_db=True)
			return werkzeug.utils.redirect('/web/reset_password?db=%s&token=%s' % (kw['db'], kw['token']))
		##############################################################################

		response = request.render('auth_signup.reset_password', qcontext)
		response.headers['X-Frame-Options'] = 'DENY'
		
		return response

	def _signup_with_values(self, token, values):
		"""
		Do not login twice
		"""
		db, login, password = request.env['res.users'].sudo().signup(values, token)
		request.env.cr.commit()