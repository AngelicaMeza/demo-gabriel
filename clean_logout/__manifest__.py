# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
	'name': 'Clean Logout',
	'description': """FIX: no authenticate twice and clean logged_in.""",
	'author': "IT Sales",
	'website': "https://www.itsalescorp.com/",
	'version': '0.1',
	'category': 'Tools',
	'depends': [
		'auth_signup',
		'restrict_logins',
		'password_security',
		'auth_session_timeout',
	],
}