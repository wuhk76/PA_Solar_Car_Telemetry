from bleak import BleakClient, BleakScanner
import asyncio
class Bledev:
    def __init__(self, address, tx_uuid, rx_uuid):
        self.address = address
        self.tx_uuid = tx_uuid
        self.rx_uuid = rx_uuid
        self.client = BleakClient(address)
        self.rx_queue = asyncio.Queue()
    def note_handler(self, sender, data):
        self.rx_queue.put_nowait(bytes(data))
    async def connect(self):
        await self.client.connect()
        await self.client.start_notify(self.rx_uuid, self.note_handler)
    async def disconnect(self):
        if self.client.is_connected:
            await self.client.stop_notify(self.rx_uuid)
            await self.client.disconnect()
    async def send(self, data):
        await self.client.write_gatt_char(self.tx_uuid, data, response = False)
    async def receive(self):
        return await self.rx_queue.get()
