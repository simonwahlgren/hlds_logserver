#!/usr/bin/env python3.6

import asyncio
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
logger.addHandler(console)

log_entry_regexp = b'^\xff\xff\xff\xfflog L ([0-9]{2}\/[0-9]{2}\/[0-9]{4} - [0-9]{2}:[0-9]{2}:[0-9]{2}): (.*)\n\x00'
log_entry_regexp = re.compile(log_entry_regexp)

PORT = 9999
EVENTS = {
    re.compile(b'^World triggered "Round_Draw"'): 'round_draw',
    re.compile(b'^World triggered "Round_End"'): 'round_end',
    re.compile(b'^World triggered "Round_Start"'): 'round_start',
    re.compile(b'^Team "CT" triggered "CTs_Win" \(CT "(\d+)"\) \(T "(\d+)"\)'): 'team_cts_win',
    re.compile(b'^Team "TERRORIST" triggered "Terrorists_Win" \(CT "(\d+)"\) \(T "(\d+)"\)'): 'team_ts_win',
}


class LogEntry:

    def _parse_data(self, data):
        match = re.match(log_entry_regexp, data)
        if match:
            date, entry = match.groups()
            logger.debug(entry)
            return date, entry

        return None, None

    def _parse_event(self, entry):
        for regexp, event in EVENTS.items():
            match = re.match(regexp, entry)
            if match:
                return event, match.groups()

        return None, None

    def parse(self, data):
        date, entry = self._parse_data(data)
        if entry:
            return self._parse_event(entry)

        return None, None


class EventHandler:

    def publish(self, data):
        event, groups = LogEntry().parse(data)
        if event:
            logger.info(f'Event {event} triggered')


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        EventHandler().publish(data)


loop = asyncio.get_event_loop()
logger.info(f'Starting HLDS logging server on port {PORT}')

listen = loop.create_datagram_endpoint(
    EchoServerProtocol, local_addr=('0.0.0.0', PORT))
transport, protocol = loop.run_until_complete(listen)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

transport.close()
loop.close()
