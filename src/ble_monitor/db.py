from datetime import datetime
from typing import List

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship

from ble_monitor.config import config
from ble_monitor.utils import ba_to_str, str_to_ba

engine = create_engine(
    f"postgresql://{config.get('PGUSER')}:"
    f"{config.get('PGPASSWORD')}@"
    f"{config.get('PGHOST')}:"
    f"{config.get('PGPORT')}/"
    f"{config.get('PGDATABASE')}",
    echo=False,
)
Base = declarative_base()


class Advertisement(Base):
    __tablename__ = "advertisement"

    id = Column(Integer, primary_key=True)
    received_at = Column(DateTime)
    device_mac = Column(LargeBinary(6), ForeignKey("device.mac"))
    service_uuid = Column(LargeBinary(config.get("service_uuid_length")))
    service_data = Column(LargeBinary)

    device = relationship("Device")

    def __repr__(self):
        return (
            f"Advertisement(id={self.id}, "
            f"received_at={self.received_at}, "
            f"device_mac={ba_to_str(self.device_mac)}, "
            f"service_uuid={self.service_uuid}, "
            f"service_data={ba_to_str(self.service_data, sep='')})"
        )


class Device(Base):
    __tablename__ = "device"

    mac = Column(LargeBinary(6), primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"Device(mac={ba_to_str(self.mac)}, name={self.name})"


def create_tables(drop: bool = False):
    if drop:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def add_devices(drop: bool = False):
    devices = [
        Device(mac=str_to_ba(d["mac"]), name=d["name"])
        for d in config.get("remote_devices")
    ]

    with Session(engine) as session:
        if drop:
            session.query(Device).delete()
        session.bulk_save_objects(devices)
        session.commit()


def add_advertisement(device_mac: str, service_uuid: str, service_data: List[int]):
    ad = Advertisement(
        received_at=datetime.now(),
        device_mac=str_to_ba(device_mac),
        service_uuid=bytearray(
            [
                int(service_uuid[i : i + 2], base=16)
                for i in range(0, len(service_uuid), 2)
            ]
        ),
        service_data=bytearray(service_data),
    )

    with Session(engine) as session:
        session.add(ad)
        session.commit()
