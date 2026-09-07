"""The POS working day.

A branch's trading day does not line up with the calendar day: it opens at the
"Working Day Start Time" configured in Selling Settings and closes at the
"Working Day End Time", which for a late-night branch falls after midnight on the
following calendar date (e.g. 10:00 -> 06:00). This module converts a working-day
date into the absolute datetime window it really covers, so a shift spanning
midnight is reported whole instead of being cut in two by posting date.

The boundary between one working day and the next is the *closing* time, not the
opening time. That keeps consecutive windows contiguous: the stretch between
closing and the next opening (06:00 to 10:00, when the branch is shut) belongs to
the day about to start, so nothing posted off-hours can fall through a gap
between two windows and disappear from every report.
"""

from __future__ import annotations

import datetime

import frappe
from frappe.utils import add_days, get_datetime, get_timedelta, getdate, now_datetime

START_FIELD = "posa_working_day_start_time"
END_FIELD = "posa_working_day_end_time"


def get_working_day_times():
	"""(start, end) working day times from Selling Settings as timedeltas.
	Returns (None, None) when either is unset, in which case callers fall back to
	plain calendar-date filtering."""
	start = get_timedelta(frappe.db.get_single_value("Selling Settings", START_FIELD))
	end = get_timedelta(frappe.db.get_single_value("Selling Settings", END_FIELD))

	if start is None or end is None:
		return None, None

	return start, end


def crosses_midnight(start, end):
	"""True when the day closes on the next calendar date, i.e. the end time is
	not strictly after the start time (10:00 -> 06:00, or a full 24h day)."""
	return start is not None and end is not None and end <= start


def format_time(offset):
	"""A working day time as HH:MM:SS. str() on a timedelta drops the leading zero
	("6:00:00"), which reads wrong next to a padded start time."""
	if offset is None:
		return None

	total = int(offset.total_seconds())
	return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def _at(day, offset):
	"""The datetime `offset` into the given calendar date."""
	return get_datetime(str(getdate(day))) + offset


def get_current_working_day(now=None):
	"""The working day that the given moment belongs to. While a day that closes
	after midnight is still running the branch is trading the previous calendar
	date, so 02:00 on the 6th reports the 5th and it only rolls over to the 6th
	once the 06:00 closing time has passed."""
	now = get_datetime(now) if now else now_datetime()
	day = getdate(now)

	start, end = get_working_day_times()
	if not crosses_midnight(start, end):
		return day

	if datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) < end:
		day = add_days(day, -1)

	return day


def get_working_day_window(from_date, to_date):
	"""Absolute datetime bounds [from, to) spanned by a range of working days.
	With a 10:00 -> 06:00 day the working day of the 5th runs from
	2026-09-05 06:00:00 up to (but not including) 2026-09-06 06:00:00.
	Returns (None, None) when no working day is configured, or when it is set to
	close on the same calendar date it opens, in which case a working day is just
	a calendar day and callers filter by date exactly as they did before."""
	start, end = get_working_day_times()
	if not crosses_midnight(start, end):
		return None, None

	return _at(from_date, end), _at(add_days(getdate(to_date), 1), end)


def get_working_day_hours(day):
	"""When the branch actually opens and closes on the given working day, as
	absolute datetimes. Distinct from get_working_day_window(): that one returns
	the reporting boundaries (close to close), these are the trading hours shown
	to the user, so a 10:00 -> 06:00 day on the 6th reads
	2026-09-06 10:00 -> 2026-09-07 06:00."""
	start, end = get_working_day_times()
	if start is None:
		return None, None

	close_day = getdate(day)
	if crosses_midnight(start, end):
		close_day = add_days(close_day, 1)

	return _at(day, start), _at(close_day, end)


def in_window(posting_date, posting_time, from_dt, to_dt):
	"""Whether a document's date and time fall inside a working-day window."""
	moment = get_datetime(str(getdate(posting_date))) + (get_timedelta(posting_time) or datetime.timedelta())
	return from_dt <= moment < to_dt


@frappe.whitelist()
def get_working_day_context(day=None, at=None):
	"""Working day configuration for the UI: the times set in Selling Settings
	plus the working day in question, so a screen can open on the previous
	calendar date while the night shift is still running.

	`day` names a working day outright. `at` gives a moment - a shift's
	period_start_date, say - and the working day it falls in is resolved here,
	on the server, rather than being recomputed from a hardcoded hour in the
	client. Neither: the working day happening now."""
	start, end = get_working_day_times()

	if day:
		working_day = getdate(day)
	elif at:
		working_day = get_current_working_day(at)
	else:
		working_day = get_current_working_day()
	from_dt, to_dt = get_working_day_window(working_day, working_day)
	opens_at, closes_at = get_working_day_hours(working_day)

	return {
		"enabled": start is not None,
		"start_time": format_time(start),
		"end_time": format_time(end),
		"crosses_midnight": crosses_midnight(start, end),
		"working_day": str(working_day),
		# Trading hours, for display.
		"opens_at": str(opens_at) if opens_at else None,
		"closes_at": str(closes_at) if closes_at else None,
		# Reporting boundaries, close to close.
		"from_datetime": str(from_dt) if from_dt else None,
		"to_datetime": str(to_dt) if to_dt else None,
	}
