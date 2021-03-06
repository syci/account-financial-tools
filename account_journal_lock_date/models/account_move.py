# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from odoo import api, models, _

from ..exceptions import JournalLockDateError


class AccountMove(models.Model):

    _inherit = 'account.move'

    @api.model
    def create(self, values):
        move = super().create(values)
        move._check_lock_date()
        return move

    @api.multi
    def write(self, values):
        self._check_lock_date()
        res = super().write(values)
        self._check_lock_date()
        return res

    def _check_lock_date(self):
        res = super()._check_lock_date()
        if self.env.context.get("bypass_journal_lock_date"):
            return res
        for move in self:
            if self.user_has_groups('account.group_account_manager'):
                lock_date = move.journal_id.fiscalyear_lock_date or date.min
            else:
                lock_date = max(
                    move.journal_id.period_lock_date or date.min,
                    move.journal_id.fiscalyear_lock_date or date.min,
                )
            if move.date <= lock_date:
                if self.user_has_groups('account.group_account_manager'):
                    message = _(
                        "You cannot add/modify entries for the journal '%s' "
                        "prior to and inclusive of the lock date %s"
                    ) % (move.journal_id.display_name, lock_date)
                else:
                    message = _(
                        "You cannot add/modify entries for the journal '%s' "
                        "prior to and inclusive of the lock date %s. "
                        "Check the Journal settings or ask someone "
                        "with the 'Adviser' role"
                    ) % (move.journal_id.display_name, lock_date)
                raise JournalLockDateError(message)
        return res
