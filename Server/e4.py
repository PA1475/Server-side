import asyncio
import enum
from e4Client import E4Handler
from enum import Enum
import inspect
import time
import csv

class E4data(Enum):
    BVP = "bvp"
    ACC = "acc"
    GSR = "gsr"
    IBI = "ibi"
    TEMP = "tmp"
    BAT = "bat"
    TAG = "tag"
    HR = "hr"

CORRECT_DATA = ["bvp","acc","gsr","ibi","tmp","bat","tag"]

STREAM_FROM = {
    E4data.BVP : "E4_Bvp",
    E4data.ACC : "E4_Acc",
    E4data.GSR : "E4_Gsr",
    E4data.TEMP: "E4_Temp",
    E4data.IBI : "E4_ibi",
    E4data.HR  : "E4_Hr",
    E4data.BAT : "E4_Battery",
    E4data.TAG : "E4_Tag"
}

def dump_data(name, signal, ts_dict, hz):
    timestamp = ts_dict[name]
    rows = [[timestamp], [hz]]
    for value in signal:
        rows.append([value])
    filename = f'../Dashboard/data/e4_wristband/{name}_{str(timestamp)}.csv'
    with open(filename, 'w') as f:
        write = csv.writer(f)
        write.writerows(rows)

def handle_e4_list(l_str):
    e4_list = []
    temp_lst = l_str.split(' | ')
    cmd_lst = temp_lst[0].split(' ')
    no_items = int(cmd_lst[2])
    if no_items > 0:
        devices = temp_lst[1:]
        for i in range(no_items):
            e4_list.append(devices[i].split(' ')[0])
    return e4_list

def handle_e4_subscription(s_str):
    if s_str.split(' ')[3] == "OK":
        return True
    return False

SECONDS_TO_SAVE = 30

class E4:
    def __init__(self):
        self._E4_client = E4Handler(self._dc_callback)
        self._connected = False
        self.dc_func = None
        self._counter_dict = {
            "EDA" : 0,
            "BVP" : 0,
            "TEMP": 0,
            "HR" : 0
        }
        self._ts_dict = {
            "EDA" : 0,
            "BVP" : 0,
            "TEMP": 0,
            "HR" : 0
        }
        self.dataObject = {
            "EDA": [],
            "BVP": [],
            "TEMP": [],
            "HR" : [],
            "timestamp": 0
        }

        self._add_callbacks()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, type, value, traceback):
        await self._E4_client.exit()

    async def exit(self):
        await self._E4_client.exit()

    def _add_callbacks(self):
        self._E4_client.callback('E4_Bvp' ,self._BVP)
        self._E4_client.callback('E4_Gsr' ,self._GSR)
        self._E4_client.callback('E4_Temperature',self._TEMP)
        self._E4_client.callback('E4_Ibi' ,self._IBI)
        self._E4_client.callback('E4_Hr' ,self._HR)
    
    def _reset_data(self):
        self.dataObject = {
            "EDA": [],
            "BVP": [],
            "TEMP": [],
            "HR" : [],
            "timestamp": 0
        }
        self._ts_dict = {
            "EDA" : 0,
            "BVP" : 0,
            "TEMP": 0,
            "HR" : 0
        }
        self._counter_dict = {
            "EDA" : 0,
            "BVP" : 0,
            "TEMP": 0,
            "HR" : 0
        }
    
    def _BVP(self, timestamp, data):
        DATA_TYPE = "BVP"
        FREQUENCY = 64
        if self._ts_dict[DATA_TYPE] == 0:
            self._ts_dict[DATA_TYPE] = time.time()
        self._counter_dict[DATA_TYPE] += 1
        
        if self._counter_dict[DATA_TYPE] == SECONDS_TO_SAVE*FREQUENCY:
            dump_data(DATA_TYPE, self.dataObject[DATA_TYPE], self._ts_dict, FREQUENCY)


        self.dataObject[DATA_TYPE].append(data[0])
        if len(self.dataObject[DATA_TYPE]) % ((SECONDS_TO_SAVE*FREQUENCY)+1) == 0:

            self.dataObject[DATA_TYPE].pop(0)
        
    def _ACC(self, timestamp, data):
        pass

    def _GSR(self, timestamp, data):
        DATA_TYPE = "EDA"
        FREQUENCY = 4
        if self._ts_dict[DATA_TYPE] == 0:
            self._ts_dict[DATA_TYPE] = time.time()
        self._counter_dict[DATA_TYPE] += 1
        
        if self._counter_dict[DATA_TYPE] == SECONDS_TO_SAVE*FREQUENCY:
            dump_data(DATA_TYPE, self.dataObject[DATA_TYPE], self._ts_dict, FREQUENCY)


        self.dataObject[DATA_TYPE].append(data[0])
        if len(self.dataObject[DATA_TYPE]) % ((SECONDS_TO_SAVE*FREQUENCY)+1) == 0:

            self.dataObject[DATA_TYPE].pop(0)

    def _TEMP(self, timestamp, data):
        if self._ts_dict["TEMP"] == 0:
            self._ts_dict["TEMP"] = time.time()

        self.dataObject["TEMP"].append(data[0])
        if len(self.dataObject["TEMP"]) % ((SECONDS_TO_SAVE*4)+1) == 0:
            self.dataObject["TEMP"].pop(0)

    def _IBI(self, timestamp, data):
        pass

    def _HR(self, timestamp, data):
        DATA_TYPE = "HR"
        FREQUENCY = 1
        if self._ts_dict[DATA_TYPE] == 0:
            self._ts_dict[DATA_TYPE] = time.time()
        self._counter_dict[DATA_TYPE] += 1
        
        if self._counter_dict[DATA_TYPE] == SECONDS_TO_SAVE*FREQUENCY:
            dump_data(DATA_TYPE, self.dataObject[DATA_TYPE], self._ts_dict, FREQUENCY)


        self.dataObject[DATA_TYPE].append(data[0])
        if len(self.dataObject[DATA_TYPE]) % ((SECONDS_TO_SAVE*FREQUENCY)+1) == 0:

            self.dataObject[DATA_TYPE].pop(0)

    def _BATTERY(self, timestamp, data):
        pass
    def _TAG(self, timestamp, data):
        pass

    async def _dc_callback(self, state):
        if state == "LOST" or state == "S_LOST":
            self._connected = False
            await self._E4_client.exit()
            self._reset_data()

        if self.dc_func is not None:
            if inspect.iscoroutinefunction(self.dc_func):
                await self.dc_func(state)
            else:
                self.dc_func(state)
    
    def disconnect_callback(self, func):
        self.dc_func = func

    async def connect_to_server(self, port=28000):
        if not self._connected:
            wait_event = asyncio.Event()
            await self._E4_client.start(port, wait_event)
            await wait_event.wait()
            self._connected = self._E4_client.ensure_connection()
        return self._connected

    async def connect_E4_device(self, d_name = "082FCD"):
        if not self._connected:
            raise Exception("Server is not connected.")
        response = await self._E4_client.send("device_connect", d_name)
        parts = response.split(' ')
        if parts[2] == "OK":
            return True
        return False
    
    async def connect_E4(self):
        if not self._connected:
            raise Exception("Server is not connected.")
        device_lst = handle_e4_list(await self._E4_client.send("device_list"))
        if device_lst:
            return await self.connect_E4_device(device_lst[0])
        return False
    
    async def disconnect_E4(self):
        """
            Returns True if device was disconnected,
            Returns False if there was no device to disconnect
            After calling this function a new connection to the
            E4 Streaming Server needs to be established
        """
        self._reset_data()
        if not self._connected:
            return True
        self._connected = False
        await self._E4_client.send("device_disconnect")
        await self._E4_client.exit()
        # No device connected in the first place
        return True
    
    async def subscribe_to(self, enum_sub):
        if not self._connected:
            raise Exception("Server is not connected.")
        sub = enum_sub.value
        success = False
        if sub in CORRECT_DATA:
            resp = await self._E4_client.send("device_subscribe", f"{sub} ON")
            if resp.split(' ')[3] == "OK":
                success = True
        return success

    async def pause_E4(self, status=True):
        """
         Returns True if the connected device was false
         Returns False if there was no connected device to pause
        """
        if not self._connected:
            raise Exception("Server is not connected.")
        msg = "OFF"
        if status:
            msg = "ON"
        response = await self._E4_client.send("pause",msg)
        if response.split(' ')[2] == "OK":
            return True
        return False
    
    def check_stream(self):
        return len(self.dataObject["HR"])

    def get_data(self, no_seconds):
        if no_seconds > SECONDS_TO_SAVE:
            raise BufferError(f"To many seconds. Only the last {SECONDS_TO_SAVE} seconds are stored.")
        if no_seconds > len(self.dataObject["HR"]) or not self._connected:
            raise IndexError("There is not enough data.")
        data_object = {}
        data_object["EDA"] = self.dataObject["EDA"][-4*no_seconds:]
        data_object["BVP"] = self.dataObject["BVP"][-64*no_seconds:]
        data_object["TEMP"] = self.dataObject["TEMP"][-4*no_seconds:]
        data_object["HR"] = self.dataObject["HR"][-1*no_seconds:]
        data_object["timestamp"] = time.time()
        return data_object



async def main():
    e4 = E4()
    e4.disconnect_callback(lambda state : print(state))
    connected = await e4.connect_to_server()
    if connected:
        await e4.connect_E4()
        await e4.subscribe_to(E4data.IBI)
        await asyncio.sleep(10)
        await e4.disconnect_E4()
    await e4.exit()

def test_dump():
    dic = {"HR" : time.time()}
    dump_data("HR", [80,80,79,80,79,80], dic, 1)

if __name__ == "__main__":
   test_dump()