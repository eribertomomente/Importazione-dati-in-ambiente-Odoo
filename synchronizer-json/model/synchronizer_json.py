# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

import urllib2, base64
import json
import logging
from pprint import pprint
import time
import datetime
import ast



_logger = logging.getLogger(__name__)


class Synchronizer_json(models.Model):
    _inherit = ['synchronizer']
    source_type = fields.Selection(selection_add=[('json', 'JSON')])

    @api.multi
    def sync_json(self, sync_id=None):
        _logger.info("inherit sync function: JSON")

        sync, result = super(Synchronizer_json, self)._validate_url(sync_id)
        
        ## converto la stringa in dizionario
        resource = json.load(result)

        return super(Synchronizer_json, self)._sync_resource(resource, sync)



    
    


