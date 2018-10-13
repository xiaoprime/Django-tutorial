import io
import os
import sys
import platform

if platform.system() == 'Windows':
    sys.path.append(r'C:\Users\mtk13028\Documents\Git\flex-private')
    sys.path.append(r'C:\Users\mtk13028\Documents\Git\flex-private/flexxamples/demos')
else:
    sys.path.append('/Users/xiaoprime/Documents/GitHub/flexx')
    sys.path.append('/Users/xiaoprime/Documents/GitHub/flexx/flexxamples/demos')
    sys.path.append('/Users/xiaoprime/Documents/GitHub/Q-learning-NW-SRCH/Simulator/')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')

import time
import re

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from flexx import flx

from matplotlib.dates import date2num, num2date
import matplotlib.dates

import pickle

import numpy as np

import glob

from module.agent import *

from lte_stored_freq import *
from mrs_common_band_table import *
from module.config import _config


if _config.get('File_Path', 'WEB_SIM_FILE_PATH'):
    WEB_SIM_FILE_PATH = r'' + _config.get('File_Path', 'WEB_SIM_FILE_PATH')

class Relay(flx.Component):
    
    number_of_connections = flx.IntProp(settable=True)
    
    def init(self):
        self.update_number_of_connections()

        self.current_idx = 0

        if platform.system() == 'Windows':
            directories = glob.glob(r'Y:\log_pool\*')
            self.ROOT_PATH = r'Y:\log_pool'
        else:
            directories = glob.glob(r'/Users/xiaoprime/Documents/GitHub/Q-learning-NW-SRCH/Simulator/log_pool/*')
            self.ROOT_PATH = r'/Users/xiaoprime/Documents/GitHub/Q-learning-NW-SRCH/Simulator/log_pool'
        
        time.sleep(1)

        directories = sorted(list(filter(lambda f: os.path.isdir(f), directories)), reverse=True)
        #self.stock_list = list(enumerate(directories, start=1))
        self.stock_list = [x.split('\\' if platform.system() == 'Windows' else '/')[-1] for x in directories]
        #self.refresh()

    @flx.manager.reaction('connections_changed')
    def update_number_of_connections(self, *events):
        n = 0
        for name in flx.manager.get_app_names():
            sessions = flx.manager.get_connections(name)
            n += len(sessions)
        self.set_number_of_connections(n)
    
    @flx.emitter
    def system_info(self, dat, stockname, otherseries=None):
        dat = dat.to_dict('split')
        dat['label'] = [str(x).split(' ')[0] for x in dat['index']]
        dat['index'] = list(date2num(dat['index']))

        dat['rec'] = {}
        dat['min'] = {}
        dat['max'] = {}
        dat['min']['index'] = np.nanmin(dat['index'])
        dat['max']['index'] = np.nanmax(dat['index'])
        for idx, tp in zip(range(len(dat['columns'])), dat['columns']):
            dat['rec'][tp] = [x[idx] for x in dat['data']]
            dat['min'][tp] = np.nanmin(dat['rec'][tp])
            dat['max'][tp] = np.nanmax(dat['rec'][tp])
        del dat['data']

        return dict(dat=dat,
                    stockname=stockname,
                    otherseries=otherseries,
                    sessions=self.number_of_connections,
                    total_sessions=flx.manager.total_sessions
                    )
  
flx.relay = Relay()

nsamples = 16

import smartms

class SmartMS(flx.PyComponent):
    
    nsamples = nsamples
    
    def init(self):
        with flx.TabLayout() as self.tabbar:
            with flx.HBox(title='A'):
                with flx.VBox(flex=0):
                    flx.Widget(flex=0)

                    flx.Label(text='Select Environment: ')
                    self.logselector = flx.ComboBox(options=flx.relay.stock_list, selected_index=0, style='width: 100%', maxsize=(500,320))
                    self.logselector.set_editable(True)
                    flx.Label(text='Basic Algorithm: ')
                    self.BasicAlgo = {}
                    self.b1 = flx.ToggleButton(text='Gen93 NWSEL')
                    self.BasicAlgo['Gen93 NWSEL'] = False
                    self.b2 = flx.ToggleButton(text='Gen97 NWSEL w.o. INTERRAT RSSI')
                    self.BasicAlgo['Gen97 NWSEL w.o. INTERRAT RSSI'] = False
                    self.b3 = flx.ToggleButton(text='Gen97 NWSEL with INTERRAT RSSI', checked=True)
                    self.BasicAlgo['Gen97 NWSEL with INTERRAT RSSI'] = True
                    flx.Label(text='Press Run: ')
                    self.button = flx.Button(text='Run')
                    self.button.reaction(self._do_work, 'pointer_down')
                    flx.Widget(flex=1)
                    flx.Label(text="Tutorial@http://wiki/display/~MTK13028/01.+Startup")
                    flx.Label(text=r"Log@\\pc17080057\log_pool")
                with flx.VBox(flex=1):
                    self.view = smartms.SmartMSView()       
            with flx.Widget(title='B'):
                self.r1 = flx.RadioButton(text='Gen93 NWSEL')
                self.r2 = flx.RadioButton(text='Gen97 NWSEL w.o. INTERRAT RSSI')
                self.r3 = flx.RadioButton(text='Gen97 NWSEL with INTERRAT RSSI', checked=True)
                flx.Label(text='Your Algorithm: ')
                with flx.VBox():
                    self.msg_edit = flx.TextAreaEdit(flex=1, placeholder_text='Enter code to simulate...\npress Shift+Enter to submit')

        
        self.text = ''

        self.log = flx.relay.stock_list[0]
        print(self.log)
        self.LTE_ENV = LTE_Environment(flx.relay.ROOT_PATH + '/' + self.log)
        self.UMTS_ENV = UMTS_Environment(flx.relay.ROOT_PATH + '/' + self.log)
        self.GSM_ENV = GSM_Environment(flx.relay.ROOT_PATH + '/' + self.log)

        self.UE = UE_Configuration(WEB_SIM_FILE_PATH, [LTE_ENV, UMTS_ENV, GSM_ENV])

        self.Agent = AgentClass(webview=self.view, env_ls=[self.LTE_ENV, self.UMTS_ENV, self.GSM_ENV], ue=self.UE)
     
    @flx.reaction('!logselector.user_selected')
    def _treeitem_selected(self, *events):
        self.log = flx.relay.stock_list[events[0]['index']]
        print(self.log)
        self.LTE_ENV.__init__(flx.relay.ROOT_PATH + '/' + self.log)
        self.UMTS_ENV.__init__(flx.relay.ROOT_PATH + '/' + self.log)
        self.GSM_ENV.__init__(flx.relay.ROOT_PATH + '/' + self.log)

        self.UE.__init__(WEB_SIM_FILE_PATH, [self.LTE_ENV, self.UMTS_ENV, self.GSM_ENV])

        self.Agent = AgentClass(webview=self.view, env_ls=[self.LTE_ENV, self.UMTS_ENV, self.GSM_ENV], ue=self.UE)

        self.Agent.resetconsole()

        flx.logger.info(self.log)

    ### send code to execute ###
    @flx.reaction('msg_edit.submit')
    def _send_message(self, *events):
        self.tabbar.set_current(0)
        LTE_ENV = self.LTE_ENV
        UMTS_ENV = self.UMTS_ENV
        GSM_ENV = self.GSM_ENV

        Agent = self.Agent
        
        code = self.msg_edit.text
        exec(code)

    @flx.reaction('b1.checked', 'b2.checked', 'b3.checked')
    def _set_algorithm(self, *events):
        ev = events[-1]
        self.BasicAlgo[ev.source.text] = ev.new_value
        flx.logger.info(ev.source.text)
        flx.logger.info(ev.new_value)

    def _do_work(self, *events):
        LTE_ENV = self.LTE_ENV
        UMTS_ENV = self.UMTS_ENV
        GSM_ENV = self.GSM_ENV

        Agent = self.Agent

        ROOT_PATH = r'C:\Users\mtk13028\Documents\Git\Q-learning-NW-SRCH\Simulator'
        code = ''
        with open(ROOT_PATH + r'\plmnsearch_test.py', 'r') as f:
            code += f.read()
        if self.BasicAlgo['Gen93 NWSEL']:
            with open(ROOT_PATH + r'\plmnsearch_93.py', 'r') as f:
                code += f.read()       
        if self.BasicAlgo['Gen97 NWSEL w.o. INTERRAT RSSI']:
            with open(ROOT_PATH + r'\plmnsearch_97.py', 'r') as f:
                code += f.read()
        if self.BasicAlgo['Gen97 NWSEL with INTERRAT RSSI']:
            with open(ROOT_PATH + r'\plmnsearch_97_INTERRAT_RSSI_n2.py', 'r') as f:
                code += f.read()

        flx.logger.info(code)
        code += self.msg_edit.text
        exec(code)


# Dump it to a dictionary of assets that we can serve. Make the main
# page index.html. The link=0 means to pack the whole app into a single
# html page (note that data (e.g. images) will still be separate).
app = flx.App(SmartMS)
assets = app.dump('index.html', link=0)

from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse(assets['index.html'].decode())