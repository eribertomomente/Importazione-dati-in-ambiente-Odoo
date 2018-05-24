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
import xml.etree.ElementTree as ET


_logger = logging.getLogger(__name__)


class Synchronizer_xml(models.Model):
    _inherit = ['synchronizer']  

    source_type = fields.Selection(selection_add=[('xml', 'XML')])

    @api.multi
    def sync_xml(self, sync_id=None):
        _logger.info("inherit sync function: XML")

        sync, result = super(Synchronizer_xml, self)._validate_url(sync_id)
        
        # converto il risultato della risorsa in stringa
        xml_data = result.read()
        ## converto la stringa xml in dizionario
        xml_data = xml_data.replace('\n', '').replace('\t', '')
        resource = self.xml_parser(ET.fromstring(xml_data))
        return super(Synchronizer_xml, self)._sync_resource(resource, sync)



    def xml_parser(self, root):
    
        dict={}
        model = root.find("model")
        if model == None:
            raise ValidationError(_("Invalid API. Model field missing"))
        dict['model'] = model.text
        for data in root.findall("data"):
            data_set = []
            for item in data.findall('item'):
                dict_set = {}
                for element in item.findall("element"):
                    name = element.get("name")
                    text = element.text
                    if text is None: # caso ricorsivo
                        dict_set[name] = self.xml_parser(element)
                    else:
                        dict_set[name] = text
                data_set.insert(0, dict_set)
            data_set.reverse()
            dict['data']= data_set
        
        return dict