import asyncio
import json
import numpy as np
import pandas as pd
from VSCServerMessages import *
import time
import os

feature_order = {
        'mean_SCL': [],
        'AUC_Phasic' : [],
        'min_peak_amplitude' : [],
        'max_peak_amplitude' : [],
        'mean_phasic_peak' : [],
        'sum_phasic_peak_amplitude' : [],
        'mean_temp' : [],
        'mean_temp_difference' : [],
        'max_temp' : [],
        'max_temp_difference' : [],
        'min_temp' : [],
        'min_temp_difference' : [],
        'difference_BVPpeaks_ampl' : [],
        'mean_BVPpeaks_ampl' : [],
        'min_BVPpeaks_ampl' : [],
        'max_BVPpeaks_ampl' : [],
        'sum_peak_ampl' : [],
        'HR_mean_difference' : [],
        'HR_variance_difference' : [],
        'label' : []
}

class Action:
    def __init__(self, frequency, serv):
        # Needs to be set when creating a new action
        
        self.NAME = "ACT1"
        self.CLIENT_ACTION = True
        self.DEVICES = []
        self.ACTIONS = []
        self.active = False
        # --------------------------------------------
        # Do not worry about these
        
        self.serv = serv
        self.main_task = None
        self._subscriptions = []
        self.client_answer_lock = asyncio.Event()
        self._client_answer_message = ""
        # --------------------------------------------
        # Available for changes during runtime in _execute()

        self.running = False
        self.time = 1/frequency
        self.settings = {
            "TIME" : self._set_time
        }
    # ------------------------------------------------
    # -------------- Core functions ------------------
    # ------------------------------------------------
    async def start(self):
        # Starts the scheduler, waits for main_task to be done
        self.running = True
        self.main_task = asyncio.create_task(self._scheduler())
        await self.main_task
    
    async def exit(self):
        # Resets variables if action is to be activated again
        shut_down = []
        if self.running:
            self.running = False
            self._client_answer_message = ""
            self.client_answer_lock.clear()
            shut_down = await self._shutdown_dependent()
            if self.main_task != None:
                # Abruptly cancel, cancels all waiting
                # coroutines
                self.main_task.cancel()
                try:
                    await self.main_task
                except asyncio.CancelledError:
                    pass
        return shut_down

    async def _scheduler(self):
        while self.running:
            # Sleeps inbetween work
            await asyncio.sleep(self.time)
            if self.running:
                # Do work
                await self._execute()
    
    # -------------------------------------
    # -------- Messaging client -----------
    # -------------------------------------

    def client_response(self, data):
        if self.running:
            # Response from client saved in class variable
            self._client_answer_message = data
            self.client_answer_lock.set()        
    
    async def _msg_client(self, data):
        # Send message to client, no response expected
        await self.serv.action_send(self.NAME, data)

    async def _msg_client_wait(self, data):
        # Send message to client and wait for response
        await self.serv.action_send_wait(self.NAME, data)
        
        await self.client_answer_lock.wait()
        self.client_answer_lock.clear()

        return self._client_answer_message

    # ---------------------------------------------
    # ------------- Safe deactivation -------------
    # ---------------------------------------------

    def observe(self, act):
        self._subscriptions.append(act)
    
    async def _shutdown_dependent(self):
        shut_down = []
        for a in self._subscriptions:
            shut_down.extend(await a.exit())
        shut_down.append(self.NAME)
        return shut_down

    # ---------------------------------------------
    # ---------------- Execution ------------------
    # ---------------------------------------------
    
    def _set_time(self, new_time):
        changed = True
        try:
            self.time = float(new_time)
        except Exception:
            changed = False
        return changed

    async def _execute(self):
        pass

class SurveyAction(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        # - - NECESSARY - -
        self.NAME = "SRVY"
        self.DEVICES = ["E4"]
        # -----------------

        self.DATA_RANGE = 10

    def _convert(self, latest_data):
        ret_dict = {}
        for key, val in latest_data.items():
            ret_dict[key] = np.array(val)
        return ret_dict

    def _save_instance(self, instance, label):
        # Check if csv file already exists
        FILE_NAME = "dataset.csv"
        df = None

        if os.path.exists(FILE_NAME):
            df = pd.read_csv(FILE_NAME)
        else:
            df = pd.DataFrame(feature_order)
        df1 = pd.DataFrame({
            'mean_SCL': [instance[0]],
            'AUC_Phasic' : [instance[1]],
            'min_peak_amplitude' : [instance[2]],
            'max_peak_amplitude' : [instance[3]],
            'mean_phasic_peak' : [instance[4]],
            'sum_phasic_peak_amplitude' : [instance[5]],
            'mean_temp' : [instance[6]],
            'mean_temp_difference' : [instance[7]],
            'max_temp' : [instance[8]],
            'max_temp_difference' : [instance[9]],
            'min_temp' : [instance[10]],
            'min_temp_difference' : [instance[11]],
            'difference_BVPpeaks_ampl' : [instance[12]],
            'mean_BVPpeaks_ampl' : [instance[13]],
            'min_BVPpeaks_ampl' : [instance[14]],
            'max_BVPpeaks_ampl' : [instance[15]],
            'sum_peak_ampl' : [instance[16]],
            'HR_mean_difference' : [instance[17]],
            'HR_variance_difference' : [instance[18]],
            'label' : [label]
        })
        df = pd.concat([df, df1], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)

    async def _execute(self):
        # Request mood from extension, wait for response
        message = await self._msg_client_wait("MOOD")
        # Get data to pair mood with
        try:
            latest_data = self.serv._E4_handler.get_data(self.DATA_RANGE)
        except Exception:
            return None
        # Add mood to data
        del latest_data["timestamp"]
        instance = self.serv._E4_model.get_instance(self._convert(latest_data))

        self._save_instance(instance, int(message))


class EstimatedEmotion(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "ESTM"
        self.DEVICES = ["E4"]
        self._signal_index = 0
        self.DATA_RANGE = 10
    
    def _convert(self, latest_data):
        ret_dict = {}
        for key, val in latest_data.items():
            ret_dict[key] = np.array(val)
        return ret_dict
    
    def _save_prediction(self, index):
        # Check if csv file already exists
        FILE_NAME = "../Dashboard/Sensors/emotions.csv"
        df = None

        if os.path.exists(FILE_NAME):
            df = pd.read_csv(FILE_NAME)
        else:
            df = pd.DataFrame({
                "timestamps" : [],
                "emotions" : []
            })
        timestamp = int(time.time())
        df1 = pd.DataFrame({
            "timestamps" : [timestamp],
            "emotions" : [index]
        })
        df = pd.concat([df, df1], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)

    async def _execute(self):
        latest_data = self.serv._E4_handler.get_data(self.DATA_RANGE)

        # Convert to correct format before using with E4Model
        signal_values = self._convert(latest_data)
        # Do stuff
        pred_lst = self.serv._E4_model.predict(signal_values)
        # Get the prediction with highest certainty
        max_pred = max(pred_lst)
        # Get index of said prediction
        pred_index = pred_lst.index(max_pred) + 1
        # Save prediction to disk, for use in Dashboard
        self._save_prediction(pred_index)
        # Send prediction to client
        msg = f"{str(pred_index)} {str(round(max_pred*100, 1))}"
        await self._msg_client(msg)

class TestAction(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "TEST"
    
    async def _execute(self):
        print(await self._msg_client_wait("Tjabba"))


