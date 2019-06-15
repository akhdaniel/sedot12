from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ConfimWizard(models.TransientModel):
    _name = 'vit.confirm_wizard'

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        emp = self.env['hr.employee']
        emp.action_sedot()
        return {'type':'ir.actions.act_window_close'}