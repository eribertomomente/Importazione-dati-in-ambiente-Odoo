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


class Synchronizer_csv(models.Model):
    _inherit = ['synchronizer']  

    source_type = fields.Selection(selection_add=[('csv', 'CSV')])

    @api.multi
    def sync_csv(self, sync_id=None):
        _logger.info("inherit sync function: CSV")

        sync, result = super(Synchronizer_csv, self)._validate_url(sync_id)
        
        # converto il risultato della risorsa in stringa
        csv_data = result.read()
        ## converto la stringa xml in dizionario
        resource = self.csv_parser(csv_data)

        return super(Synchronizer_csv, self)._sync_resource(resource, sync)



    def csv_parser(self, csv_string):
        res = {}  
        csv = csv_string.split()

        # first line of csv with fields names
        definition = csv[0].split(",")
        del csv[0]

        models=[]
        data=[]
        for line in csv:
            words = line.split(",")
            data_dict={}
            models.insert(-1,words[0])
            for i in range(len(definition)):
                data_dict[definition[i]]=words[i]
            data.insert(len(data), data_dict)

        model=models[0]
        for model_item in models:
            if model_item != model:
                raise ValidationError(_('Invalid csv data: all records must be related to the same model'))

        res["model"]=model
        res["data"]=data

        return res