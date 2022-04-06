import asyncio
import time
from bleak import BleakClient
from bleak import BleakScanner

"""
Handle lookup:
    PPG(BVP) : 19
    EDA : 23
    ACC : 27
    ST : 31
    Empaticalnk command : 36
    Empaticalnk Control : 40
    Battery : 44
"""


E4_ADDRESS = "88:6B:0F:CD:2F:08"
CONTROL_CMD = 36

NOTIFY_DATA = [19, 23, 31]

class E4:

    def __init__(self):
        self.dataObject = {
                "EDA": [],
                "BVP": [],
                "ST": [],
                "timestamp": 0
                }

    async def scan_for_e4(self):
        scanner = BleakScanner()
        searching = True
        count = 4
        wristband = []
        while searching and count >= 0:
            devices = await scanner.discover()
            count -= 1
            for i in range(len(devices)):
                tmp = str(devices[i]).split(" ")[1]
                if tmp == "Empatica":
                    if str(devices[i]).split(" ")[0][:-1] not in wristband:
                        wristband.append(str(devices[i]).split(" ")[0][:-1])
        return wristband

    def disconnected(self, client):
        return

    # handle BVP data
    def bvp_handler(self, data):
        print(data)

    # handle EDA data
    def eda_handler(self, data):
        print(data)

    # handle ST data
    def st_handler(self, data):
        result = []
        for i in range(0, 18, 2):
            result.append(data[i]*0.02+data[i+1]*5.12-273.15)
        print(result)

    def notify_func(self, sender, data):
        # if sender == 19 (BVP)
        if sender == 19:
            self.bvp_handler(list(data))
        # if sender == 23 (EDA)
        elif (sender == 23):
            self.eda_handler(list(data))
        # if sender == 31 (ST)
        elif (sender == 31):
            self.st_handler(list(data))
        # fallback
        else:
            print(f"{sender}: {list(data)}")

    async def connect(self, deviceId):
        scanner = BleakScanner()
        await scanner.start()
        self.client = BleakClient(deviceId)
        try:
            await self.client.connect()
            if self.client.is_connected:
                self.client.set_disconnected_callback(self.disconnected)
                tasks = []
                for ntify in NOTIFY_DATA:
                    tasks.append(self.client.start_notify(ntify, self.notify_func))

                tasks.append(self.client.write_gatt_char(36, bytearray(
                    [1]+list(round(time.time()).to_bytes(8, 'little'))[:-4])))
                await asyncio.gather(*tasks)
                await scanner.stop()
        except Exception as e:
            pass

        while True:
            if not self.client.is_connected:
                break
            await asyncio.sleep(5)


async def main():
    E4Object = E4()
    address = await E4Object.scan_for_e4()
    await E4Object.connect(address[0])

if __name__ == "__main__":
    asyncio.run(main())
    #asyncio.run(scanner())
