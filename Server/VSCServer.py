from Error_handler import ErrorHandler
from VSCMessageHandler import MsgHandler
from VSCServerMessages import *
from ActionFactory import action_factory
from e4_data import E4data
import asyncio
import sys, os
import json
import os
import pandas as pd
import numpy as np
import pandas as pd
from e4 import E4


sys.path.append(os.path.join(os.path.dirname(__file__), "../machine_learning"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(os.path.join(os.path.dirname(__file__), "./Eyetracker"))

import machine_learning
import machine_learning.retrain as ml_retrain
from gazepoint import Livestream


BASELINE_TIME = 30 # Last 30 seconds
BASELINE_NAME = os.path.join(os.path.dirname(__file__), "lokal_baseline.json")


class VSCServer:
    def __init__(self, port=1337):
        self.errh = ErrorHandler()

        is_dummy = False
        if len(sys.argv) > 1:
            if sys.argv[1] == "True":
                is_dummy = True

        self._E4_handler = E4()
        self._E4_model = None
        self.eye_tracker = Livestream()
        self._retrain = False
        self._baseline = None
        self._retrain = False
        self._auto_save = False
        self.settings = {
            "devices" : {"E4" : False, "EYE" : False, "EEG" : False, "TEST" : False, "TEST2" : False},
            "setup" : True
        }
        self.actions = action_factory(self)
        self.act_waiting = {}
        self.msg_handler = MsgHandler(port, self._handle_incomming_msg)
        self.handler_task = None
        self.handler_task = asyncio.create_task(self.msg_handler.start())
        
        self.done_lock = asyncio.Event()
        self.cmd_dict = {
            "CE4" : self._connect_E4,             # Connect E4
            "DE4" : self._disconnect_E4,          # Disconnect E4
            "ONEY": self._start_eyetracker,       # Start EYE
            "OFEY": self._stop_eyetracker,        # Stop EYE
            "RCEY": self._recalibrate_eyetracker, # Recalibrate EYE
            "END" : self._end_server,             # End server (exit)
            "SBL" : self._start_baseline,         # Start basline recording
            "AACT": self._activate_action,        
            "DACT": self._deactivate_action,
            "EACT": self._edit_action,
            "ACT" : self._action_response,
            "RTAI": self._set_retrain,
            "ASAI": self._auto_save_training
        }

    
    async def run(self):
        try:
            await self.handler_task
        except asyncio.CancelledError:
            pass
        finally:
            await self._E4_handler.exit()
            self._kill_eyetracker()
        
        if self._retrain:
            self._retrain_ai(self._auto_save)
        print("Server shutdown successful")




    def _activation_check(self, act):
        def actions_traverse(visited, current):
            visited.add(current)
            if not self.actions[current].ACTIONS:
                return visited
            for a in self.actions[current].ACTIONS:
                if not a in visited:
                    visited.update(actions_traverse(visited, a))
            return visited

        for d in self.actions[act].DEVICES:
            if not self.settings["devices"][d]:
                return []
        
        return list(actions_traverse(set(), act))

    async def _activate_action(self, msg):
        # Desired actions splitted with a space
        action_lst = msg.split(' ')
        if action_lst == ['']:
            action_lst = []
        # action which device(s) are not connected
        cannot_activate = []
        for a in action_lst:
            if a in self.actions:
                depend_act = self._activation_check(a)
                print("Activating: " + str(depend_act))
                # Check that all required devices are connected
                for d in depend_act:
                    if not self.actions[d].running:
                        self.actions[d].active = True
                        asyncio.create_task(self.actions[d].start())
                if not depend_act and self.actions[a].CLIENT_ACTION:
                    cannot_activate.append(a)
        if cannot_activate:
            # Return all actions which could not be connected
            not_activated = " ".join(cannot_activate)
            await self.send(f"{ACTIVATE_ACTION} {FAIL_STR} {not_activated}")
        else:
            # All actions are active 
            await self.send(f"{ACTIVATE_ACTION} {SUCCESS_STR}")

    async def _deactivate_action(self, msg):
        action_lst = msg.split(' ')
        if action_lst == ['']:
            action_lst = []
        client_actions = []
        # Deactivate all actions
        for act in action_lst:
            if act in self.actions:
                shut_down = await self.actions[act].exit()
                print("Shutting down: " + str(shut_down))
                for a in shut_down:
                    self.actions[a].active = False
                    if self.actions[a].CLIENT_ACTION:
                        client_actions.append(a)
                    if a in self.act_waiting:
                        del self.act_waiting[a]
        deactivated = " ".join(client_actions)
        await self.send(f"{DEACTIVATE_ACTION} {SUCCESS_STR} {deactivated}")
    
    async def _edit_action(self, data):
        cmd_parts = data.split(" ")
        a = cmd_parts[0]
        if not a in self.actions:
            await self._send_error(ERR_NOT_AN_ACTION, a)
            return
        cmd_parts = cmd_parts[1:]
        not_changed = []
        not_a_setting = []
        for i in range(0,len(cmd_parts), 2):
            s = cmd_parts[i]
            if s in self.actions[a].settings:
                changed = self.actions[a].settings[s](cmd_parts[i+1])
                if not changed:
                    not_changed.append(s)
            else:
                not_a_setting.append(s)
        response = ""
        if not_a_setting:
            response = " ".join(not_a_setting)
            await self._send_error(ERR_NOT_A_SETTING,response)
        if not_changed:
            not_chngd = " ".join(not_changed)
            await self.send(f"{EDIT_ACTION} {FAIL_STR} {not_chngd}")
        if not (not_a_setting or not_changed):
            await self.send(f"{EDIT_ACTION} {SUCCESS_STR}")

    async def _handle_incomming_msg(self, msg):
        # Message format CMD {Data}
        data = ""
        seperator = msg.find(" ")
        # Command to call
        if seperator == -1:
            cmd = msg
        else:
            cmd = msg[:seperator]
        # Data sent to the function mapped to the command
        data = msg[seperator+1:]
        if cmd in self.cmd_dict:
            # Call function with data
            await self.cmd_dict[cmd](data)
        else:
            # Throw error, non existant command
            print(msg)
            await self._send_error(ERR_INVALID_CMD)
    
    async def _send_error(self, err, msg=""):
        # Send error to client
        await self.msg_handler.send(f"{self.errh[err]} {msg}")
    
    async def action_send(self, act, data):
        # Send data to extension from action, one way communication
        msg = f"{ACTION_STR} {act} {data}"
        await self.send(msg)

    async def action_send_wait(self, act, data):
        msg = f"{ACTION_STR} {act} {data}"
        # Put the action in waiting list
        self.act_waiting[act] = self.actions[act].client_response
        await self.send(msg)

    async def _action_response(self, msg):
        seperator = msg.find(" ")
        # Action name is first argument is msg
        name = msg[:seperator]
        data = msg[seperator+1:]
        if name in self.act_waiting:
            # Send response to client
            self.act_waiting[name](data)
            # Remove action from waiting list
            del self.act_waiting[name]

    
    async def send(self, msg):
        await self.msg_handler.send(msg)

    async def _save_baseline(self, baseline):
        with open(BASELINE_NAME,"w") as opfile:
            json.dump(baseline, opfile, indent=4)

    def _to_baseline(self, stream_data):
        ret_dict = {}
        for key, val in stream_data.items():
            if key != "timestamp":
                ret_dict[key] = np.array(val)
            else:
                ret_dict[key] = val
        return ret_dict

    def load_lokal_baseline(self):
        dic = {}
        if os.path.exists(BASELINE_NAME):
            with open(BASELINE_NAME,"r") as opfile:
                dic = self._to_baseline(json.load(opfile))
        return dic

    async def _start_baseline(self, data):
        # Record baseline, subscribe to feed
        # Make sure E4 is connected
        cmd_lst = data.split(" ")
        if cmd_lst[0] != "NEW":
            # Try to load to already recorded baseline
            baseline = self.load_lokal_baseline()
            if not baseline:
                await self.send(f"{START_BASELINE} {FAIL_STR} OLD")
            else:
                self._baseline = baseline
                self._E4_model = machine_learning.E4model(self._baseline)
                await self.send(f"{START_BASELINE} {SUCCESS_STR} OLD")
        else:
            # Check if E4 is connected
            if self.settings["devices"]["E4"]:
                await asyncio.sleep(BASELINE_TIME+10)
                try:
                    stream_data = self._E4_handler.get_data(BASELINE_TIME)
                except BufferError:
                    await self._send_error(ERR_E4_DATA_RAISE)
                    return
                except IndexError:
                    await self.send(f"{START_BASELINE} {FAIL_STR} NEW")
                    return
                self._baseline = self._to_baseline(stream_data)
                await self._save_baseline(stream_data)

                # Create E4 prediction model
                self._E4_model = machine_learning.E4model(self._baseline)
                await self.send(f"{START_BASELINE} {SUCCESS_STR} NEW")
            else:
                # Let extension know that connection to E4 is required to create
                # a new baseline
                await self.send(f"{START_BASELINE} {FAIL_STR} CE4")

    async def _end_server(self, data):
        await self._save_actions()
        await self._E4_handler.exit()
        try:
            self.msg_handler.exit()
            self.handler_task.cancel()
        except asyncio.exceptions.CancelledError:
            pass
    
    async def _activate_active_actions(self):
        for a in self.actions.keys():
            all_devices_connected = True
            for d in self.actions[a].DEVICES:
                if not self.settings["devices"][d]:
                    all_devices_connected = False
            if self.actions[a].active and all_devices_connected:
                await self.actions[a].start()

    async def _lost_E4(self, data):
        if data == "LOST" or data == "S_LOST":
            if self.settings["devices"]["E4"]:
                self.settings["devices"]["E4"] = False
                await self._exit_actions("E4")
                print("Lost connection to E4.")
                await self.send(f"{DISCONNECT_E4} {SUCCESS_STR} {data}")
        
    
    async def _connect_E4(self, data):
        self._E4_handler.disconnect_callback(self._lost_E4)
        connected = await self._E4_handler.connect_to_server(data)
        if connected:
            connected = await self._E4_handler.connect_E4()
            if connected:
                await self._E4_handler.subscribe_to(E4data.BVP)
                await self._E4_handler.subscribe_to(E4data.GSR)
                await self._E4_handler.subscribe_to(E4data.IBI)
                await self._E4_handler.subscribe_to(E4data.TEMP)
                self.settings["devices"]["E4"] = True
                print("Connected to E4.")
                await self.send(f"{CONNECT_E4} {SUCCESS_STR}")
            else:
                print("No E4 device available.")
                await self.send(f"{CONNECT_E4} {FAIL_STR} DEVICE")
        else:
            print("Cannot connect to E4 Streaming Server.")
            await self.send(f"{CONNECT_E4} {FAIL_STR} SERVER")


    async def _exit_actions(self, device, deactivate=False):
        for a in self.actions:
            if device in self.actions[a].DEVICES:
                await self.actions[a].exit()
                print(f"Shutting {a}.")
                if a in self.act_waiting:
                    del self.act_waiting[a]
                if deactivate:
                    self.actions[a].active = False


    async def _disconnect_E4(self, data):
        self.settings["devices"]["E4"] = False
        await self._exit_actions("E4")
        await self._E4_handler.disconnect_E4()
        print("Disconnected E4.")
        await self.send(f"{DISCONNECT_E4} {SUCCESS_STR}")


    async def _start_eyetracker(self, data):
        try:
            self.eye_tracker.run(True, int(data))
            self.settings["devices"]["EYE"] = True
            await self._activate_active_actions()
            print("Eyetracker connected.")
            await self.send(f"{START_EYE} {SUCCESS_STR}")
        except Exception as e:
            print(e)
            await self.send(f"{START_EYE} {FAIL_STR}")
    
    def _kill_eyetracker(self):
        self.eye_tracker.run(False)
        
    async def _stop_eyetracker(self, data):
        print("Turning off eyetracker")
        await self._exit_actions("EYE")
        self.eye_tracker.run(False)
        self.settings["devices"]["EYE"] = False
        print("Eyetracker disconnected.")
        await self.send(f"{STOP_EYE} {SUCCESS_STR}")

    async def _recalibrate_eyetracker(self, data):
        if self.eye_tracker.gazetracker is not None:
            # Make into function in LiveStream object
            self.eye_tracker.gazetracker.tracker.calibrate()
            await self.send(f"{RECALIBRATE_EYE} {SUCCESS_STR}")
        else:
            await self.send(f"{RECALIBRATE_EYE} {FAIL_STR}")
    
    async def _ai_retraining(self, data):
        self._retrain = False
        log_msg = "OFF"
        if data == "true":
            log_msg = "ON"
            self._retrain = True
        print(f"Retrain AI turned {log_msg}.")
    
    def _retrain_ai(self, auto_save=False):
        FILE_NAME = "dataset.csv"
        console_msg = "Retraining AI..."
        if auto_save:
            console_msg += " Closing when done."
        if os.path.exists(FILE_NAME):
            print(console_msg)
            df = pd.read_csv("dataset.csv")
            ml_retrain.train(df, auto_save)
        

    async def _set_retrain(self, data):
        self._retrain = False
        if data == "true":
            self._retrain = True
    
    async def _auto_save_training(self, data):
        self._auto_save = False
        if data == "true":
            self._auto_save = True


async def main():
    server = VSCServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass