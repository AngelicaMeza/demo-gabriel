# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, models, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request
from datetime import datetime

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
	_inherit = "res.users"
	
	@classmethod
	def _login(cls, db, login, password):
		if not password:
			raise AccessDenied()
		ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
		try:
			with cls.pool.cursor() as cr:
				self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
				with self._assert_can_auth():
					user = self.search(self._get_login_domain(login))
					if not user:
						raise AccessDenied()
					user = user.with_user(user)
					user._check_credentials(password)
					if user.sid and user.logged_in:
						_logger.warning("User %s is already logged in into the system!. Multiple sessions are not allowed for security reasons!" % user.name)
						request.uid = user.id
						raise AccessDenied("already_logged_in")
					# save user session detail if login success and not password has expired
					if not user._password_has_expired():
						user._save_session()
					user._update_last_login()
		except AccessDenied:
			_logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
			raise
		_logger.info("Login successful for db:%s login:%s from %s", db, login, ip)
		return user.id

	@api.model
	def _auth_timeout_session_terminate(self, session):
		"""Pluggable method for terminating a timed-out session

		This is a late stage where a session timeout can be aborted.
		Useful if you want to do some heavy checking, as it won't be
		called unless the session inactivity deadline has been reached.

		Return:
			True: session terminated
			False: session timeout cancelled
		"""
		if session.db and session.uid:
			request.env.cr.execute("""UPDATE res_users SET sid = FALSE, logged_in = FALSE WHERE id = %s""" % self.id)
			session.logout(keep_db=True)
		return True