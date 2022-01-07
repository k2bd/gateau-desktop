from typing import Awaitable, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from gateau_desktop.emulator_listener import RAM


class RamEvent(BaseModel):
    """
    A change in a subscribed RAM location
    """

    #: Location in memory
    location: int

    #: Old value, or None if this is the first frame
    old: Optional[int]

    #: New value
    new: int


class RamChangeInfo(BaseModel):
    #: New frame value
    frame: int

    #: Old frame value, if any
    old_frame: Optional[int]

    #: Change events
    events: List[RamEvent]


@runtime_checkable
class OnRamChange(Protocol):
    def __call__(self, info: RamChangeInfo) -> Awaitable[None]:
        ...


class RamMonitor(BaseModel):
    """
    Class that monitors RAM frames for changes at subscribed addresses,
    and invokes ``on_ram_change`` with a list of change events if there are
    any.
    """

    class Config:
        arbitrary_types_allowed = True

    #: List of memory addresses to subscribe to
    subscription: List[int]

    #: Callback function to invoke when subscribed RAM has changed between
    #: observed frames
    on_ram_change: OnRamChange

    #: Latest processed RAM frame
    latest_frame: Optional[RAM] = None

    async def ram_frame_handler(self, ram: RAM) -> None:
        """
        Handle a new frame of RAM. Can be used as the ``on_ram_frame`` callback
        for an EmulatorListener.
        """
        # Don't process old frames
        if self.latest_frame and ram.frame <= self.latest_frame.frame:
            return

        old_ram = self.latest_frame
        self.latest_frame = ram

        #: If this is the first frame, everything's a change
        if not old_ram:
            events = [
                RamEvent(location=byte.location, old=None, new=byte.value)
                for byte in ram.ram_data
                if byte.location in self.subscription
            ]
            await self.on_ram_change(
                info=RamChangeInfo(
                    frame=ram.frame,
                    old_frame=None,
                    events=events,
                )
            )
            return

        old_by_addr = {
            byte.location: byte.value
            for byte in old_ram.ram_data
            if byte.location in self.subscription
        }
        new_by_addr = {
            byte.location: byte.value
            for byte in ram.ram_data
            if byte.location in self.subscription
        }

        events = []
        for addr, new_value in new_by_addr.items():
            old_value = old_by_addr.get(addr)
            if new_value != old_value:
                events.append(
                    RamEvent(
                        location=addr,
                        old=old_value,
                        new=new_value,
                    )
                )

        if events:
            await self.on_ram_change(
                info=RamChangeInfo(
                    frame=ram.frame,
                    old_frame=old_ram.frame,
                    events=events,
                )
            )
