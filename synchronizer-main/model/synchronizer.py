# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

import urllib2, base64
import json
import logging
import pprint
import time
import datetime
import ast
import sys

_logger = logging.getLogger(__name__)


class Synchronizer(models.Model):

    _name = 'synchronizer'

    name = fields.Char('Name', required=True)
    src = fields.Char('URL/Source', required=True)
    src_params = fields.Char('Params')
    basic_auth_username = fields.Char('Username')
    basic_auth_password = fields.Char('Password')
    source_type = fields.Selection([], string='Source type', required=False)
    cron_id = fields.Many2one(string='Odoo Cron', comodel_name='ir.cron', 
                readonly=True)
    record_properties = fields.Text('Properties')
    model_hierarchy = fields.Text('Hierarchy')
    optional_header = fields.Text('Optional Header')

    # override create to create a cron after synchronizer creation, link back the syncronizer
    # cron: giornaliero, disattivo  
    @api.model
    def create(self, context=None):
        res = super(Synchronizer, self).create(context)
        cron = self.env['ir.cron'].create(
            {
                "name": res.name + " cron", 
                "next_call": self.create_date, 
                "user_id": "1", 
                "interval_number": "1", 
                "interval_type": "days",
                "active": "False", 
                "model": "synchronizer",
                "function": "sync", 
                "sync_id": ([res.id])
            }
        )
        res.cron_id = cron
        return res

    # unlink
    # eliminazione ricorsiva del cron e dei syncronizer record
    @api.multi
    def unlink(self):
        for record in self:
            # elimino il cron associato
            cron = record.env['ir.cron'].browse(record.cron_id.id)
            cron.unlink()
            # procedo a eliminare tutti i sync record associati
            objs = record.env['synchronizer_record'].search([('synchronizer_id', '=', record.id)])
            for record in objs:
                record.unlink()
        # elimino il/i synchronizer
        return super(Synchronizer, self).unlink()

    # NUKE: eliminazione ricorsiva dei dati importati
    @api.multi
    def nuke(self):
        _logger.info("nuke function")
        # clean and convert the string into a list of model names
        models_list = self.model_hierarchy.replace(",", "").split()
        # reverse  in order to start nuke from the bottom of the hierarchy
        models_list = list(reversed(models_list))

        for record in self:
            for model in models_list:
                # search related objects
                # by model and synchronizer_id
                sync_rec_objs = self.env["synchronizer_record"].search(
                    [
                        ('odoo_model', '=', model),
                        ('synchronizer_id', '=', record.id)
                    ]
                )

                # clean related objects
                related_ids = []
                for rec in sync_rec_objs:
                    related_ids.append(rec.odoo_id)

                self.env[model].browse(related_ids).unlink()

                # clean sync records
                sync_rec_objs.unlink()

        self.unlink()

    #spezzo la funzine sync in 2 parti per permettere il riutilizzo del codice ai figli
    @api.multi
    def sync(self, sync_id=None):

        _logger.info("sync function")

        if self.source_type is False:
            return {
                'type': 'ir.actions.act_window.message',
                'title': _("Errore: impossibile sincronizzare"),
                'message': _("Selezionare il formato dati o installare il modulo figlio synchronizer specifico"),
                'close_button_title': _('Close')
            }

        return eval("self.sync_"+self.source_type+"(sync_id)")

        


    def _validate_url(self, sync_id):
        ## sostituire self con una variabile (sync)
        ## verificare manualmente se è passato un id 
        if type(sync_id) == int:
            sync = self.env['synchronizer'].browse(sync_id)

        else:
            ## oppure self è uno solo
            self.ensure_one()
            ## altrimenti solleva eccezione
            sync=self

        url = sync.src
        ## add parametres to URL

        if '?' not in url:
            # no parameters has ben added yet
            url = url + '?'
        if '&' in url:
            # some parametres has already been added
            # let's add '&' to add others
            url = url + '&'

        if sync.src_params:
            url = url + sync.src_params 
            url = url + '&'

        url = sync._add_custom_parameters(url)

        ## TODO
        ## implement a logic switch between XML and Json API 
        ## each programming logic will be moved to a private method 
        ## when implemented the XML parser will return a dictionary foarmatted as the Json dictionary

        if(not 'file://' in url and not 'http://' in url and not 'https://' in url):
            raise ValidationError(_('invalid url or source: parh must start with http/https or file'))

        # check if everything worked fine
        _logger.info(url)

        # parte json
        resource = False
        # search file locally in /tmp
        if('file://' in url):
            resource = sync._get_local_resource(url)
        else:
            ## search file remote
            resource = sync._get_remote_resource(url)

        return sync, resource

    def _get_local_resource(self, path):
        try:

            full_path = ('/tmp/' + path.replace('file://', '')).split('?')[0]
            with open(full_path, 'r') as result:

                ## restituisco risorsa senza parsing
                return open(result.name)

        except Exception as inst:
            #TODO cambiare il msg JSON ma verificare che sta funzione non legga json da somewhere
            raise ValidationError(_("Attention! path not valid, file not found in /tmp or invalid JSON format"))


    ## this function gets a json object from an url
    def _get_remote_resource(self, url):
        try:

            request = urllib2.Request(url)

            # gestisco basic auth
            if self.basic_auth_username:

                username = self.basic_auth_username
                password = self.basic_auth_password

                base64string = base64.b64encode('%s:%s' % (username, password))

                request.add_header("Authorization", "Basic %s" % base64string)

            ## gestisco header opzionali
            # + validazione del json
            if self.optional_header:
                # converto la stringa in un dizionario
                optional_header_dict = json.loads(self.optional_header)
                # aggiungo il dizionario agli headers
                for key in optional_header_dict:
                    request.add_header(key, optional_header_dict[key])

            ## carico stringa da API remota
            resource = urllib2.urlopen(request)
            ## restituisco risorsa senza parsing
            return resource

        except urllib2.HTTPError:
            raise ValidationError(_("Attention! Url not valid or invalid data with the format specified"))

    def _sync_resource(self, resource, sync):
        ### extract informations from the resource
        counter = {"records":0,"inserts":0,"updates":0,"errors":0,"errors_ext_ids":[]}
        hierarchy, query_result, counter, objects_processed = sync._create_or_update_records(resource, [], counter, None)
        ## serialize hierarchy with json
        ser_hierarchy = json.dumps(hierarchy)
        ## clean the string to be more readeable
        formatted_ser_hierarchy = ser_hierarchy.strip('[]').replace('"', '')
        sync.model_hierarchy = formatted_ser_hierarchy

        ## odoo interface can reach the timeout limit
        ## logger return message so you can still read the result
        _logger.info("""
            -----------------------------------
            Import result:
             %s records read
             %s inserts
             %s updates
             %s errors
             error ids: %s
            -----------------------------------
        """ % ( counter["records"], counter["inserts"], counter["updates"], counter["errors"], pprint.pformat(counter['errors_ext_ids']) ))

        ## return function result to interface
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Message'),
            'message': _("Import result: %s records read, %s inserts, %s updates, %s errors; error ids: %s" % 
                    (counter["records"], counter["inserts"], counter["updates"], counter["errors"], pprint.pformat(counter['errors_ext_ids']))),
            'close_button_title': _('Close')
        }


    def _add_custom_parameters(self, url):
        ## add last imported id
        url = url + "last_id=0" + "&"
        ## add last write date
        url = url + "last_date='2000-01-01'"
        return url

    
    ## at every step of recursion add the model to 
    ## this function create or updates model record (from the API given) and related synchronizer_record
    def _create_or_update_records(self, resource, hierarchy, counter, objects_processed):
        
        if not resource:
            _logger.info("empty resource, nothing to do")
            return hierarchy, False, counter, None
        
        # model
        if resource.has_key("model"):
            model = resource.get("model")
            hierarchy.append(model)
        else:
            _logger.warning("Invalid API. Model field missing")
            raise ValidationError(_("Invalid API. Model field missing"))

        # data or query
        query = []
        data = []

        if(not resource.has_key("data") and not resource.has_key("query")):
            _logger.warning("Invalid API. Data or query field missing")
            raise ValidationError(_("Invalid API. Data or query field missing"))

        if(resource.has_key("data") and resource.has_key("query")):
            _logger.warning("Invalid API. Data and query are mutually exclusive")
            raise ValidationError(_("Invalid API. Data and query are mutually exclusive"))

        ## in case of QUERY
        if resource.has_key("query"):
            query = resource.get("query")

            ## reset hierarchy
            del hierarchy[-1]

            ## perform query 
            result = self.env[model].search(query)

            _logger.info('QUERY')
            _logger.info(pprint.pformat(query))
            _logger.info(pprint.pformat(result))

            result_id = False
            if result.ids:
                if model == "synchronizer_record":
                    result_id = result[0].odoo_id
                else:
                    result_id = result[0].id

            return hierarchy, result_id, counter, None

        ## in case of DATA
        if resource.has_key("data"):
            data = resource.get("data")

        ## reset hierarchy if not data
        if not data:
            del hierarchy[-1]

        ## get model data info
        one2many_fields = {}
        many2one_fields = {}
        recalc_tree = False
        fields_objects = self.env['ir.model.fields'].search([('model_id.model', '=', model)])
        for field in fields_objects:
            if field.name == 'parent_left':
                ## mark recalc tree
                recalc_tree = True
            if field.ttype == 'one2many':
                one2many_fields[field.name] = field.relation_field
            if field.ttype == 'many2one':
                many2one_fields[field.name] = field.relation

        ## loops every property of the dictionary
        ## searching for dicts objects:
        ## in case of a dict object this function calls a self recursion
        for record in data:

            counter["records"] += 1
            save_status_ok = True

            ## this temp dict stores "clean" values of the destination object
            clean_record = {}
            write_record = {}
            ext_id = None

            ## raise error if clean_record does not contain an "id" key
            if not record.has_key("id"):
                _logger.warning("Invalid API. Id field missing")
                raise ValidationError(_("Invalid API. Id field missing"))

            for key in record:

                ## we use 'skip' to allow empty returns from query
                query_result = 'skip'

                if key == "id":
                    ext_id = record[key]
                else:
                    if not isinstance(record[key], dict):
                        clean_record[key] = record[key]
                    else:
                        hierarchy, query_result, counter, objects_processed = self._create_or_update_records(record[key], hierarchy, counter, None)

                        if((key in many2one_fields.keys() or key in one2many_fields.keys()) and query_result == 'skip'):
                            if(objects_processed):
                                clean_record[key] = objects_processed.id
                            else:
                                clean_record[key] = False

                        elif(query_result != 'skip'):
                            clean_record[key] = query_result
                        else:
                            clean_record[key] = False

                        
            # add to clean_record 
            # optional properties from eval of self.record_properties
            if self.record_properties:
                ser_properties = ast.literal_eval(self.record_properties)
                for prop in ser_properties:
                    clean_record[prop] = ser_properties[prop]


            ## with clean_record 
            ## apply create or update logic
            ## using synchronizer_record as a "support" data structure

            ## 0) cerco se l'oggetto è già stato importato 
            # (usando la chiave univoca composta da odoo_model ed ext_id)
            has_been_created = self.env['synchronizer_record'].search(
                [('odoo_model','=', model), ('ext_id','=', ext_id)]
            )

            ## gestisco opzione "noupdate" sulla chiave
            for key in clean_record:
                key_parts = key.split('|')
                clean_key = key_parts[0]
                noupdate = (len(key_parts) > 1 and key_parts[1] == 'noupdate')

                ## inserisco in write
                ## solo se non è noupdate
                ## o è un insert
                if(not noupdate or not has_been_created):

                    ## metto da parte le one2many
                    if(key in one2many_fields.keys()):
                        _logger.info('one2many prop %s not supported' % key)
                    if(key in many2one_fields.keys() and not isinstance(clean_record[key], (int,long))):
                        write_record[clean_key] = clean_record[key].id if clean_record[key] else False
                    else:
                        write_record[clean_key] = clean_record[key]
 
            obj = None
            ## 1) se l'oggetto non esiste
            if not has_been_created:
                _logger.info("create ext_id %s %s" % (ext_id, pprint.pformat(write_record)))

                ##   1.a) creo l'oggetto
                try:
                    obj = self.env[model].create(write_record)
                    ##   1.b) creo il sync record sfruttando i dati dell'oggetto creato
                    self.env['synchronizer_record'].create({
                            "synchronizer_id" : self.id,
                            "odoo_id": obj.id,
                            "ext_id": ext_id,
                            "odoo_model": model,
                            "creation_date": datetime.datetime.now(), 
                            "sync_date": datetime.datetime.now()
                        })
                    counter["inserts"] += 1

                except Exception as inst:
                    
                    counter["errors"] += 1
                    counter['errors_ext_ids'].append(ext_id)
                    _logger.info("%s" % inst)

                    obj = None
                    save_status_ok = False

            ## 2) se l'oggetto esiste
            else:
                _logger.info("update ext_id %s id %s %s" % (ext_id, has_been_created.odoo_id, pprint.pformat(write_record)))

                ##   2.a) tramite il sync record recuperato recupero anche l'oggetto vero e proprio
                try:
                    obj = self.env[model].browse([has_been_created.odoo_id])

                    ##   2.b) aggiorno tutte le proprietà dell'oggetto recuperato 
                    # e aggiorno il sync record per la sola data di sync
                    obj.write(write_record)
                    has_been_created.write({"sync_date": datetime.datetime.now()})
                    counter["updates"] += 1
                    
                except Exception as inst:
                    
                    counter["errors"] += 1
                    counter['errors_ext_ids'].append(ext_id)
                    _logger.info("%s" % inst)

                    obj = None
                    save_status_ok = False

            if(save_status_ok):
                self.env.cr.commit()
            else:
                self.env.cr.rollback()

            ## force tree recalc
            ## if we found hierarchy levels (parent tree)
            if(obj and recalc_tree):

                try:
                    _logger.info("recalc tree")
                    self.env.cr.execute("select fix_parent(%s, 'parent_id', 'name')", ((model.replace('.', '_'),)))
                    self.env.cr.commit()
                except Exception as inst:
                    
                    _logger.info("%s" % inst)
                    self.env.cr.rollback()

        return hierarchy, 'skip', counter, obj


