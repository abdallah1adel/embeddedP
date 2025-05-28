with open("log.csv", "w") as f:
  f.write("timestamp,address,temp,humidity,status\n")

import time
import random

# Virtual I2C Bus (shared memory map)
virtual_bus = {}

# Sensor Node Simulation
class SensorNode:
        def __init__(self, address, bus, malicious=False, spoof_address=None):
            self.address = address
            self.bus = bus
            self.malicious = malicious
            self.spoof_address = spoof_address

        def read_sensor(self):
            if self.malicious:
                # Fake values
                temp = round(random.uniform(80.0, 999.9), 2)
                humidity = round(random.uniform(0.0, 5.0), 2)
            else:
                temp = round(random.uniform(20.0, 45.0), 2)
                humidity = round(random.uniform(10.0, 60.0), 2)
            return {"temp": temp, "humidity": humidity}

        def send_data(self):
            data = self.read_sensor()
            addr = self.spoof_address if self.spoof_address else self.address
            self.bus[addr] = data
            print(f"[Sensor {self.address}] Sent to {addr}: {data}{' (MALICIOUS)' if self.malicious else ''}")

# Master Node Simulation
class MasterNode:
  
    def __init__(self, bus, sensor_addresses):
        self.bus = bus
        self.sensor_addresses = sensor_addresses
        self.trust_scores = {addr: 5 for addr in sensor_addresses}
        self.quarantined = set()

    def is_anomalous(self, data):
        temp = data['temp']
        humidity = data['humidity']
        return temp > 60.0 or temp < 15.0 or humidity < 5.0

    def log_data(self, addr, data, status):
        with open("log.csv", "a") as f:
            f.write(f"{time.time()},{addr},{data['temp']},{data['humidity']},{status}\n")

    def poll_sensors(self):
        readings = {}

        for addr in self.sensor_addresses:
            if addr in self.quarantined:
                print(f"[Master] Skipping quarantined sensor {addr}")
                continue

            data = self.bus.get(addr, None)

            if data:
                if self.is_anomalous(data):
                    self.trust_scores[addr] -= 1
                    status = "ANOMALOUS"
                    print(f"[! ALERT] Anomalous from {addr}: {data} | Trust: {self.trust_scores[addr]}")
                else:
                    self.trust_scores[addr] += 1
                    status = "OK"
                    print(f"[Master] Valid from {addr}: {data} | Trust: {self.trust_scores[addr]}")

                if self.trust_scores[addr] <= 0:
                    self.quarantined.add(addr)
                    print(f"[!! QUARANTINE] Sensor {addr} disabled due to repeated anomalies.")

                readings[addr] = data
                self.log_data(addr, data, status)
            else:
                print(f"[Master] No data from {addr}")

# --- Simulation Start ---
sensors = [
  
      SensorNode("0x01", virtual_bus),              # normal
      SensorNode("0x02", virtual_bus),              # normal
      SensorNode("0x03", virtual_bus, malicious=True, spoof_address="0x02"),  # BAD GUY
  
]

master = MasterNode(virtual_bus, ["0x01", "0x02", "0x03"])

# Run simulation for 5 cycles
for cycle in range(5):
  
    print(f"\n--- Cycle {cycle + 1} ---")
    for sensor in sensors:
        sensor.send_data()

    time.sleep(1)
    master.poll_sensors()
    time.sleep(1)