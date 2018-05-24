from openerp import http, _
from openerp.http import request
from requests.auth import HTTPBasicAuth
import base64
import json
import logging
import string
import random
import pprint
_logger = logging.getLogger(__name__)

class MyController(http.Controller):



    def _random_generator(self, size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))



    @http.route('/test_generator', type="http", auth="public")
    def my_test_generator(self, model, data_format, last_id=None, last_date=None):
        _logger.info("calling test generator")

        if model == "res.partner":
            return self._gen_res_partner(data_format)
        elif model == "res.partner.bank":
            return self._gen_res_partner_bank(data_format)
        elif model == "res.bank":
            return self._gen_res_bank(data_format)
        else:
            _logger.warning("Other models not supported yet")
            return {}


    def _gen_res_partner(self,data_format):

        if data_format == 'json':
            data_id= self._random_generator(3, string.digits)
            data_name = "API_test_" + self._random_generator()
            data = [{
                    "id": str(data_id), 
                    "name": data_name, 
                    "invoice_warn": "no-message", 
                    "notify_email": "always", 
                    "own_lot_counting": "1" 
                    }]

            test_object = { "model": "res.partner", "data": data }
            return json.dumps(test_object)

        elif data_format =='xml':
            data_id= self._random_generator(3, string.digits)
            data_name = "API_test_" + self._random_generator()

            data='<root><model>res.partner</model><data><item>'
            data+='<element name="id">'+str(data_id)+'</element>'
            data+='<element name="name">'+data_name+'</element>'
            data+='<element name="invoice_warn">no-message</element>'
            data+='<element name="notify_email">always</element>'
            data+='<element name="own_lot_counting">1</element>'
            data+='</item></data></root>'

            return data

        elif data_format == 'csv':
            data="model,id,name,invoice_warn,notify_email,own_lot_counting\n"
            for i in range(3):
                data_id= self._random_generator(3, string.digits)
                data_name = "API_test_" + self._random_generator()
                data+="res.partner,"+str(data_id)+","+data_name+",no-message,always,1\n"

            return data

        else:
            _logger.warning("Other formats not supported yet")
            return {}

    def _gen_res_partner_bank(self, data_format):

        if data_format == 'json':
            data_id= self._random_generator(3, string.digits)
            data_acc_number = "API_test_" + self._random_generator()
            data = [{
                    "id": str(data_id), 
                    "acc_number": data_acc_number,
                    "state": "bank"
                    }]

            test_object = { "model": "res.partner.bank", "data": data }
            return json.dumps(test_object)

        elif data_format =='xml':
            data_id= self._random_generator(3, string.digits)
            data_acc_number = "API_test_" + self._random_generator()

            data='<root><model>res.partner.bank</model><data><item>'
            data+='<element name="id">'+str(data_id)+'</element>'
            data+='<element name="acc_number">'+data_acc_number+'</element>'
            data+='<element name="state">bank</element>'
            data+='</item></data></root>'

            return data

        elif data_format == 'csv':
            data="model,id,acc_number,state\n"
            for i in range(3):
                data_id= self._random_generator(3, string.digits)
                data_acc_number = "API_test_" + self._random_generator()
                data+="res.partner.bank,"+str(data_id)+","+data_acc_number+",bank\n"

            return data

        else:
            _logger.warning("Other formats not supported yet")
            return {}

    def _gen_res_bank(self, data_format):

        if data_format == 'json':
            data_id= self._random_generator(3, string.digits)
            data_name = "API_test_" + self._random_generator()
            data = [{
                    "id": str(data_id), 
                    "name": data_name
                    }]

            test_object = { "model": "res.bank", "data": data }
            return json.dumps(test_object)

        elif data_format =='xml':
            data_id= self._random_generator(3, string.digits)
            data_name = "API_test_" + self._random_generator()

            data='<root><model>res.bank</model><data><item>'
            data+='<element name="id">'+str(data_id)+'</element>'
            data+='<element name="name">'+data_name+'</element>'
            data+='</item></data></root>'
            
            return data

        elif data_format == 'csv':
            data="model,id,name\n"
            for i in range(3):
                data_id= self._random_generator(3, string.digits)
                data_name = "API_test_" + self._random_generator()
                data += "res.bank,"+str(data_id)+","+data_name+"\n"
            return data

        else:
            _logger.warning("Other formats not supported yet")
            return {}

            
