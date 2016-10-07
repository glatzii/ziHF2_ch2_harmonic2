# -*- coding: utf-8 -*-
"""
Name
----------------------------------------------------------------------------
Created on Thu Oct 06 15:56:36 2016
Version: 0.1
@author: Thomas Glatzl

Changes
----------------------------------------------------------------------------
"""

'''
Import section
----------------------------------------------------------------------------
'''
import time, visa, datetime, sys
import pandas as pd
import numpy as np
import zhinst.ziPython, zhinst.utils    #can be found on the homepage of zurich instruments!

'''
Initial section
----------------------------------------------------------------------------
'''
# set up communication with the funtion generator via visa
rm = visa.ResourceManager()
dg1022 = rm.open_resource("USB0::0x0400::0x09C4::DG1D171100665::INSTR")
time_delay = 0.2  #time delay for the funtion generator, it needs some time between the commands

# Open connection to ziServer (Zurich lock in manual)
daq = zhinst.ziPython.ziDAQServer('localhost', 8005)
# Detect device
device = zhinst.utils.autoDetect(daq)
#set log
daq.setDebugLevel(0)

#set channels parameters for the lock in!
channel_settings = [
        [['/', device, '/sigins/0/diff'], 0],
        [['/', device, '/sigins/0/imp50'], 0],
        [['/', device, '/sigins/0/ac'], 0],
        [['/', device, '/sigins/0/range'], 2],

        [['/', device, '/sigins/1/diff'], 0],
        [['/', device, '/sigins/1/imp50'], 0],
        [['/', device, '/sigins/1/ac'], 0],
        [['/', device, '/sigins/1/range'], 2],

        [['/', device, '/oscs/0/freq'], 10],
        [['/', device, '/oscs/1/freq'], 10],

        [['/', device, '/sigouts/0/add'], 0],
        [['/', device, '/sigouts/0/on'], 0],
        [['/', device, '/sigouts/0/range'], 0],
        [['/', device, '/sigouts/0/amplitudes/6'],0],

        [['/', device, '/sigouts/1/add'], 0],
        [['/', device, '/sigouts/1/on'], 0],
        [['/', device, '/sigouts/1/range'],0],
        [['/', device, '/sigouts/1/amplitudes/7'],0],

        [['/', device, '/plls/0/adcselect'], 0],
        [['/', device, '/plls/0/enable'], 1],
        [['/', device, '/demods/0/oscselect'], 0],
        [['/', device, '/demods/1/oscselect'], 0],
        [['/', device, '/demods/2/oscselect'], 0],

        [['/', device, '/plls/1/adcselect'], 0],
        [['/', device, '/plls/1/enable'], 1],
        [['/', device, '/demods/3/oscselect'], 1],
        [['/', device, '/demods/4/oscselect'], 1],
        [['/', device, '/demods/5/oscselect'], 1],

        [['/', device, '/demods/0/rate'], 450],
        [['/', device, '/demods/1/rate'], 450],
        [['/', device, '/demods/2/rate'], 450],
        [['/', device, '/demods/3/rate'], 450],
        [['/', device, '/demods/4/rate'], 450],
        [['/', device, '/demods/5/rate'], 450],

        [['/', device, '/demods/0/enable'], 1],
        [['/', device, '/demods/1/enable'], 0],
        [['/', device, '/demods/2/enable'], 0],
        [['/', device, '/demods/3/enable'], 1],
        [['/', device, '/demods/4/enable'], 0],
        [['/', device, '/demods/5/enable'], 0],

        [['/', device, '/demods/3/harmonic'], 2]

        ]

'''
Define section
----------------------------------------------------------------------------
'''
class channels(object):
    '''
    class for the phaseshift depending on the frequency
    '''
    
    def __init__(self,f_gen, Phi_gen, f_ch1, R_ch1, Phi_ch1, f_ch2, R_ch2, 
                 Phi_ch2,phi_delta_abs,phi_delta_rel, dt):
        
        self.f_gen = f_gen          #frequency sent to the function generator
        self.Phi_gen = Phi_gen      #phaseshift sent to the function generator
        self.f_ch1 = f_ch1          #channel 1 measured frequency
        self.R_ch1 = R_ch1          #channel 1 measured abs
        self.Phi_ch1 = Phi_ch1      #channel 1 measured phase
        self.f_ch2 = f_ch2          #channel 2 measured frequency
        self.R_ch2 = R_ch2          #channel 2 measured abs
        self.Phi_ch2 = Phi_ch2      #channel 2 measured phase
        self.phi_delta_abs = phi_delta_abs      #phase difference absolute
        self.phi_delta_rel = phi_delta_rel      #phase difference relative
        self.dt = dt                #time between measurements
        
    def clear(self):
        '''
        clear the class after measurement
        '''
        
        self.f_gen = list()
        self.Phi_gen = list()
        self.f_ch1 = list()
        self.R_ch1 = list()
        self.Phi_ch1 = list()
        self.f_ch2 = list()
        self.R_ch2 = list()
        self.Phi_ch2 = list()
        self.phi_delta_abs = list()
        self.phi_delta_rel = list()
        self.dt = list()
        
        
class Oscilloscope(object):
    '''
    Oscilloscopeobject from the HF2LI for adjusting and programming
    '''
    def __init__(self,device,daq):
        self.device=device
        self.daq=daq
    
    def set_parameters(self, channel=0,bwlimit=0,samplerate=15,trigchannel=0,
                       trigedge=1,trigholdoff=0.01,triglevel=1622):
        settings = [
            [['/', self.device, '/scopes/0/channel'], channel],
            [['/', self.device, '/scopes/0/bwlimit'], bwlimit],
            [['/', self.device, '/scopes/0/time'], samplerate],
            [['/', self.device, '/scopes/0/trigchannel'], trigchannel],
            [['/', self.device, '/scopes/0/trigedge'], trigedge],
            [['/', self.device, '/scopes/0/trigholdoff'], trigholdoff],
            [['/', self.device, '/scopes/0/triglevel'], triglevel],
        ]
                
        self.daq.set(settings)
        self.daq.setDebugLevel(0) # enable logging
        # wait 1s
        time.sleep(1)
        #clean queue
        self.daq.flush()
            
    def grab_XY(self):
            '''
            grabs all needed values of the lock in
            '''
            sample_ch1 = daq.getSample('/%s/demods/0/sample' % self.device)
            f_ch1 = sample_ch1['frequency']
            R_ch1 = np.sqrt(sample_ch1['x']**2 + sample_ch1['y']**2)
            Phi_ch1 = np.arctan2(sample_ch1['y'],sample_ch1['x'])*(180.0/np.pi)
            
            sample_ch2 = daq.getSample('/%s/demods/3/sample' % self.device)
            f_ch2 = sample_ch2['frequency']
            R_ch2 = np.sqrt(sample_ch2['x']**2 + sample_ch2['y']**2)
            Phi_ch2 = np.arctan2(sample_ch2['y'],sample_ch2['x'])*(180.0/np.pi)
            
            return f_ch1, R_ch1, Phi_ch1, f_ch2, R_ch2, Phi_ch2   
            
class waveform(object):
    '''
    class of the waveform function
    '''
    def __init__(self, function, frequency, amplitude_unit, amplitude_voltage, 
                 offset, phase, channel):
        self.function = function
        self.frequency = frequency
        self.amplitude_unit = amplitude_unit
        self.amplitude_voltage = amplitude_voltage
        self.offset = offset
        self.phase = phase
        self.channel = channel            

def set_DG1022(w):
    '''
    Sends the values from the waveform class to the instrument
    ''' 
    if w.channel == 1:
        
        time.sleep(time_delay)    
        dg1022.write('APPL:%s %f,%f,%f' % (w.function, w.frequency, w.amplitude_voltage, 
                                           w.offset))
        time.sleep(time_delay)
        dg1022.write('VOLT:UNIT %s' % w.amplitude_unit) 
        time.sleep(time_delay)
        dg1022.write('PHAS %f' % w.phase)
        time.sleep(time_delay) 
        dg1022.write('OUTP ON')
        time.sleep(time_delay)
        dg1022.write('PHAS:ALIGN')
        time.sleep(time_delay) 
    
    else:
        
        time.sleep(time_delay)    
        dg1022.write('APPL:%s:CH2 %f,%f,%f' % (w.function, w.frequency, w.amplitude_voltage, 
                                               w.offset))
        time.sleep(time_delay)
        dg1022.write('VOLT:UNIT:CH2 %s' % w.amplitude_unit) 
        time.sleep(time_delay)
        dg1022.write('PHAS:CH2 %f' % w.phase)
        time.sleep(time_delay) 
        dg1022.write('OUTP:CH2 ON')
        time.sleep(time_delay)
        dg1022.write('PHAS:ALIGN')
        time.sleep(time_delay) 


def sync_DG1022(PHI,f):
    '''
    update phase and frequency
    '''
    global values
    
    values.f_gen.append(f)
    values.Phi_gen.append(PHI)
    
    f2 = f * 2.0
    time.sleep(time_delay)
    dg1022.write('APPL:SIN %f' % f)
    time.sleep(time_delay)
    dg1022.write('PHAS 0')
    time.sleep(time_delay)
    dg1022.write('APPL:SIN:CH2 %f' % f2)
    time.sleep(time_delay)
    dg1022.write('PHAS:CH2 %f' % PHI)
    time.sleep(time_delay)    
    dg1022.write('PHAS:ALIGN') 
    time.sleep(time_delay)    

def read_values():
    
    numerical_HF2LI = osci.grab_XY()
    values.f_ch1.append(numerical_HF2LI[0][0])
    values.R_ch1.append(numerical_HF2LI[1][0])
    values.Phi_ch1.append(numerical_HF2LI[2][0]) 
    values.f_ch2.append(numerical_HF2LI[3][0])
    values.R_ch2.append(numerical_HF2LI[4][0])
    values.Phi_ch2.append(numerical_HF2LI[5][0])
    print 'reading done - phi_ch2:',values.Phi_ch2[-1]
    
def save_values():
    
    global values
    
    data = {'f_gen' : values.f_gen,
            'Phi_gen' : values.Phi_gen,
              'f_ch1' : values.f_ch1,
              'R_ch1' : values.R_ch1,
              'Phi_ch1' : values.Phi_ch1,
              'f_ch2' : values.f_ch2,
              'R_ch2' : values.R_ch2,
              'Phi_ch2' : values.Phi_ch2,
              'phi_delta_abs' : values.phi_delta_abs,
              'phi_delta_rel' : values.phi_delta_rel,
              'dt' : values.dt,
              }
              
    df = pd.DataFrame(data, columns=['f_gen','Phi_gen','f_ch1','R_ch1','Phi_ch1',
    'f_ch2','R_ch2','Phi_ch2','phi_delta_abs','phi_delta_rel','dt'])
    writerstring = 'data\Phaseshift_ch2_harmonic2\Phaseshift_ch2_harmonic2_' + str(int(values.f_gen[-1])) + '.xls'
    writer = pd.ExcelWriter(writerstring)
    df.to_excel(writer,'data')
    writer.save()
    hdfstring = 'f'+str(int(values.f_gen[-1]))
    store[hdfstring]=df

    
def calc_error():
    
    global values
    
    phi_gen = np.array(values.Phi_gen)
    phi_ch2 = np.array(values.Phi_ch2)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        values.phi_delta_abs = np.abs(phi_gen - phi_ch2)
        values.phi_delta_rel = values.phi_delta_abs / phi_gen * 100.0
        values.phi_delta_rel[values.phi_delta_rel == np.inf] = 0

'''
Run section
----------------------------------------------------------------------------
'''
#lockin object
osci = Oscilloscope(device,daq)
daq.set(channel_settings)

time.sleep(1)

values = channels(list(),list(),list(),list(),list(),list(),list(),list(),list(),
                  list(),list())

w1 = waveform('SIN',1000.0,'VPP',2.0, 0.0, 0.0, 1)
w2 = waveform('SIN',2000.0,'VPP',2.0, 0.0, 0.0, 2)

set_DG1022(w1)
set_DG1022(w2)

frequencies = np.arange(100,1010,10)
phases = np.arange(0,181,1)

store = pd.HDFStore('data\Phaseshift_ch2_harmonic2\HDFPhaseshift_ch2_harmonic2.h5')
    
starttime_ges = datetime.datetime.now()

for frequency in frequencies:
    print 'f:',frequency
    for phase in phases:
       starttime_mes = datetime.datetime.now()
       #sometimes the function generator reports an I/O Error
       try:                         
           sync_DG1022(phase,frequency)
       except:
            e = sys.exc_info()[0]
            errorstring = 'f:'+str(values.f_gen[-1])+',p:'+str(values.Phi_gen[-1])
            text_file = open("Error.txt", "a")    
            text_file.write("Measurment Error!%s \n" % errorstring)    
            text_file.close()
            print "Error!", e
            pass    
           
       print 'phi:',phase
       if frequency < 300:
           time.sleep(2)
       time.sleep(2)       
       read_values()
       stoptime_mes = datetime.datetime.now()
       dt_mes = stoptime_mes - starttime_mes
       values.dt.append(dt_mes.total_seconds())
    time.sleep(1)
    calc_error()
    time.sleep(0.1)
    save_values()
    values.clear()

stoptime_ges = datetime.datetime.now()
duration_ges = stoptime_ges - starttime_ges

print 'Duration:', duration_ges.total_seconds(),'sec'
text_file = open("Finish.txt", "a")    
text_file.write("Measurment done in %s seconds \n" % str(duration_ges.total_seconds()))    
text_file.close()

store.close()

    

    



