# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta
from functools import partial
from pytz import utc
from odoo import models, _

def make_aware(dt):
	""" Return ``dt`` with an explicit timezone, together with a function to
		convert a datetime to the same (naive or aware) timezone as ``dt``.
	"""
	if dt.tzinfo:
		return dt, lambda val: val.astimezone(dt.tzinfo)
	else:
		return dt.replace(tzinfo=utc), lambda val: val.astimezone(utc).replace(tzinfo=None)

class ResourceCalendar(models.Model):
	_inherit = "resource.calendar"

	def plan_minutes(self, minutes, day_dt, compute_leaves=False, domain=None, resource=None):
		"""
		`compute_leaves` controls whether or not this method is taking into
		account the global leaves.

		`domain` controls the way leaves are recognized.
		None means default value ('time_type', '=', 'leave')

		Return datetime after having planned minutes
		"""
		day_dt, revert = make_aware(day_dt)

		# which method to use for retrieving intervals
		if compute_leaves:
			get_intervals = partial(self._work_intervals, domain=domain, resource=resource)
		else:
			get_intervals = self._attendance_intervals

		if minutes >= 0:
			delta = timedelta(hours=14)
			for n in range(100):
				dt = day_dt + delta * n
				for start, stop, meta in get_intervals(dt, dt + delta):
					interval_minutes = (stop - start).total_seconds() / 60
					if minutes <= interval_minutes:
						return revert(start + timedelta(minutes=minutes))
					minutes -= interval_minutes
			return False
		else:
			minutes = abs(minutes)
			delta = timedelta(days=14)
			for n in range(100):
				dt = day_dt - delta * n
				for start, stop, meta in reversed(get_intervals(dt - delta, dt)):
					interval_minutes = (stop - start).total_seconds() / 60
					if minutes <= interval_minutes:
						return revert(stop - timedelta(minutes=minutes))
					minutes -= interval_minutes
			return False