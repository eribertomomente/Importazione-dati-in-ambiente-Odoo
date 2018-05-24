# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

import logging
import pprint
_logger = logging.getLogger(__name__)

class SynchronizerRecord(models.Model):

    _name = 'synchronizer_record'

    _sql_constraints = [
                     ('field_unique', 
                      'unique(odoo_model, ext_id)', 
                      'Impossible to import two elements of the same model with the same ID!')
                    ]

    synchronizer_id = fields.Many2one('synchronizer', string="Synchronizer ID", required=True)
    odoo_id = fields.Integer('Id of the imported record')
    odoo_model = fields.Char('Model of the imported record')
    ext_id = fields.Integer('Id of the external record')
    creation_date = fields.Datetime(string="Creation date", select=True)
    sync_date = fields.Datetime(string="Sync date", select=True)