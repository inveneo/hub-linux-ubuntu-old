import logging
import cgi
import os
import shutil

from configurationserver.lib.base import *

log = logging.getLogger(__name__)

class AdminController(BaseController):

    ###########################
    # helper methods
    ###########################
    def Get_initial_config(config = model.Config()):
        config.mac = 'deaddeadbeef'
        config.timezone = DEFAULT_DB_ATTRS['INV_TIME_ZONE']
        config.ntp_on = DEFAULT_DB_ATTRS['INV_NTP_ON']
        config.ntp_servers = DEFAULT_DB_ATTRS['INV_NTP_SERVERS']
        config.proxy_on = DEFAULT_DB_ATTRS['INV_PROXY_ON']
        config.http_proxy = DEFAULT_DB_ATTRS['INV_HTTP_PROXY']
        config.http_proxy_port = DEFAULT_DB_ATTRS['INV_HTTP_PROXY_PORT']
        config.https_proxy = DEFAULT_DB_ATTRS['INV_HTTPS_PROXY']
        config.https_proxy_port = DEFAULT_DB_ATTRS['INV_HTTPS_PROXY_PORT']
        config.ftp_proxy = DEFAULT_DB_ATTRS['INV_FTP_PROXY']
        config.ftp_proxy_port = DEFAULT_DB_ATTRS['INV_FTP_PROXY_PORT']
        config.phone_home_on = DEFAULT_DB_ATTRS['INV_PHONE_HOME_ON']
        config.phone_home_reg = DEFAULT_DB_ATTRS['INV_PHONE_HOME_REG']
        config.phone_home_checkin = DEFAULT_DB_ATTRS['INV_PHONE_HOME_CHECKIN']
        config.locale = DEFAULT_DB_ATTRS['INV_LOCALE']
        config.single_user_login = DEFAULT_DB_ATTRS['INV_SINGLE_USER_LOGIN']

        return config

    Get_initial_config = staticmethod(Get_initial_config)
    

    ###########################
    # instance  helper methods
    ###########################    
    def get_config_entry_by_id_or_mac_or_create(self, key):
        key = str(key)

        log.debug('Key: ' + key)

        o_q = model.Session.query(model.Config)
        if len(key) == 12:
            try:
                q = o_q.filter(model.Config.mac == key).one()
            except:
                q = model.Config()
                q.mac = 'deaddeadbeef'
        else:
            q = o_q.get(key)
                
        if str(type(q)) == NONE_TYPE: # this code stinks
            q = model.Config()

        return q
       
    def validate_configuration(self, config, is_edit):
        log.debug('config validation')
        error = {}

        if not is_edit:
            try:
                model.Session.query(model.Config).filter(model.Config.mac == config.mac).one()
                error['mac'] = 'MAC is already being used'
            except:
                pass

        if not h.validate_with_regexp(MAC_REGEXP, config.mac, True, log):
            error['mac'] = 'MAC address must be 12 hex lower case values, no separator' 
        if not h.validate_with_regexp(LOCALE_REGEXP, config.locale, True, log):
            error['locale'] = 'Must be a valid locale string. E.g. en_UK.utf-8'
        if not h.validate_number(0, 65535, config.http_proxy_port, log):
            error['http_proxy_port'] = 'Must be valid port number: 0 to 65535'
        if not h.validate_number(0, 65535, config.https_proxy_port, log):
            error['https_proxy_port'] = 'Must be valid port number: 0 to 65535'
        if not h.validate_number(0, 65535, config.ftp_proxy_port, log):
            error['ftp_proxy_port'] = 'Must be valid port number: 0 to 65535'

        return error

    def copy_reset_config(self, dir):
        for f in os.listdir(dir):
            if str(f).endswith('.tar.gz'):
                log.debug(dir + '../blank.tar.gz' + ' overwrites  ' + f)
                shutil.copyfile(dir + '../blank.tar.gz', dir + '/' + f)


    ###########################
    # controller methods
    ###########################    

    def index(self):
        return redirect_to('/admin/dashboard')

    def dashboard(self):
        return render('/admin/dashboard.mako')

    def reset_client_config(self, id):
        q = self.get_config_entry_by_id_or_mac_or_create(id)
        q = self.Get_initial_config(q)

        model.Session.update(q)
        model.Session.commit()

        self.copy_reset_config(h.get_config_dir_station())
        self.copy_reset_config(h.get_config_dir_user())

        return redirect_to('/admin/dashboard')

    def set_initial_config(self):
        return self.edit(DEADDEADBEEF)

    def edit(self, id):
        c.Config = self.get_config_entry_by_id_or_mac_or_create(id)
        c.Edit = True
        return render('/admin/config_edit.mako')

    def config_remove(self, id):
        mac = str(id)

        if mac == NONE:
            log.error('Need a valid unique mac identifier')
            return

        try:
            q = model.Session.query(model.Config).filter(model.Config.mac == mac).one()
            model.Session.delete(q)
            model.Session.commit()
        except:
            return

        return redirect_to('/admin/list')

    def config_add(self):
        c.Config = model.Config()
        c.Edit = False
        return render('/admin/config_edit.mako'
)
    def config_edit_process(self, id):
        newconfig_q = self.get_config_entry_by_id_or_mac_or_create(id)
        is_edit = False

        try:
            newconfig_q.mac = cgi.escape(request.POST['mac'])
        except:
            is_edit = True
        newconfig_q.timezone = cgi.escape(request.POST['timezone'])
        newconfig_q.ntp_on = h.is_checkbox_set(request, 'ntp_on', log)
        newconfig_q.ntp_servers = cgi.escape(request.POST['ntp_servers']) 
        newconfig_q.proxy_on = h.is_checkbox_set(request, 'proxy_on', log)
        newconfig_q.http_proxy = cgi.escape(request.POST['http_proxy']) 
        newconfig_q.http_proxy_port = cgi.escape(request.POST['http_proxy_port']) 
        newconfig_q.https_proxy = cgi.escape(request.POST['https_proxy']) 
        newconfig_q.https_proxy_port = cgi.escape(request.POST['https_proxy_port']) 
        newconfig_q.ftp_proxy = cgi.escape(request.POST['ftp_proxy']) 
        newconfig_q.ftp_proxy_port = cgi.escape(request.POST['ftp_proxy_port']) 
        newconfig_q.phone_home_on = h.is_checkbox_set(request, 'phone_home_on', log)
        newconfig_q.phone_home_reg = cgi.escape(request.POST['phone_home_reg']) 
        newconfig_q.phone_home_checkin = cgi.escape(request.POST['phone_home_checkin']) 
        newconfig_q.locale = cgi.escape(request.POST['locale']) 
        newconfig_q.single_user_login = h.is_checkbox_set(request, 'single_user_login', log)
        
        error = self.validate_configuration(newconfig_q, is_edit)

        if len(error) == 0:
            model.Session.save(newconfig_q)
            model.Session.commit()
        else:
            c.Error = error
            c.Edit = False
            c.Config = newconfig_q
            return render('/admin/config_edit.mako')

        return redirect_to('/admin/config_edit_done')

    def config_edit_done(self):
        return redirect_to('/admin/list')
        
    def list(self):
        config_q = model.Session.query(model.Config)
        c.Configs = config_q.all()
        return render('/admin/list.mako')



try:
    model.Session.query(model.Config).filter(model.Config.mac == 'deaddeadbeef').one()
except:
    newconfig_q = AdminController.Get_initial_config()
        
    model.Session.save(newconfig_q)
    model.Session.commit()
