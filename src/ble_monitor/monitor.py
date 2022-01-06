import logging

from gi.repository import GLib
from pydbus import SystemBus

from ble_monitor.config import config
from ble_monitor.db import add_advertisement

_logger = logging.getLogger(__name__)


def handle_signal_fired(sender, object, iface, signal, params):
    # Check sender
    for d in config.get("remote_devices"):
        if object.startswith(
            f"/org/bluez/{config.get('adapter')}/dev_{d['mac'].replace(':', '_')}"
        ):
            device_mac = d["mac"]
            break
    else:
        _logger.debug("Ignoring device %s", object)
        return

    # Retrieve data dict
    service_datas = params
    for idx in config.get("params_indices"):
        try:
            service_datas = service_datas[idx]
        except (IndexError, KeyError):
            _logger.debug("Index %s not found", idx)
            return

    # Extract data entries
    for uuid in config.get("service_uuids"):
        try:
            service_data = service_datas[
                next(filter(lambda x: x.startswith(uuid), service_datas.keys()))
            ]

            _logger.debug(" ".join(str(hex(v)) for v in service_data))

            # The following lines are for Xiaomi thermometers with custom firmware
            # _logger.debug(f"Temp.: {(service_data[6] + 256 * service_data[7]) / 100}")
            # _logger.debug(f"Hum.: {(service_data[8] + 256 * service_data[9]) / 100}%")
        except KeyError:
            _logger.debug("Service UUID %s not found", uuid)
            return

        # Apply mask
        masked_data = []
        mask = config.get("data_mask")
        if mask is not None:
            indices = mask.split(",")
            for idx in indices:
                if "-" in idx:
                    start, stop = idx.split("-")
                    if len(start):
                        start = int(start)
                    else:
                        start = None
                    if len(stop):
                        stop = int(stop)
                    else:
                        stop = None
                    masked_data.extend(service_data[start:stop])
                else:
                    masked_data.append(service_data[int(idx)])
        else:
            masked_data = service_data

        # Write to database
        _logger.info("Writing service %s to database", uuid)
        add_advertisement(
            device_mac=device_mac, service_uuid=uuid, service_data=masked_data
        )


def start_monitor():
    bus = SystemBus()
    adapter = bus.get("org.bluez", config.get("adapter"))
    adapter.SetDiscoveryFilter({"Transport": GLib.Variant("s", "le")})

    loop = GLib.MainLoop()

    try:
        adapter.StartDiscovery()
        with bus.subscribe(sender="org.bluez", signal_fired=handle_signal_fired):
            loop.run()
    finally:
        adapter.StopDiscovery()
