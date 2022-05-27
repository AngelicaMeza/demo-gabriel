# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home

class LoginAttempts(Home):

	@http.route()
	def web_login(self, redirect=None, **kw):
		response = super(LoginAttempts, self).web_login(redirect=redirect, **kw)
		if response.qcontext.get('error'):
			# Get LoginAttempts in session
			login_attempts = request.session.get('loginAttempts')
			if not login_attempts:
				login_attempts = 0
			# If user have done more than three login attemps
			if int(login_attempts) >= 2:
				# We search the user
				user = request.env['res.users'].search([('login','=',kw.get('login'))])
				if user:
					# If we found it, you desactive it
					user.write({'active': False})
					login_attempts = -1
					response.qcontext['error'] = "%s . %s" %(response.qcontext.get('error'), _('Your account is deactivate. Please contact the administrator'))
					# ... Send here an email to the administrator
					# ... And other action that you want to make
			request.session['loginAttempts'] = login_attempts + 1

		return response