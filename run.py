#!/usr/bin/env python3

import asyncio
import dill
import logging
import os
import re

from redis import StrictRedis

redis = StrictRedis(os.getenv('REDIS_HOST', 'localhost'))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
logger.addHandler(console)

log_entry_regexp = re.compile(
    b'^\xff\xff\xff\xfflog L ([0-9]{2}\/[0-9]{2}\/[0-9]{4} - [0-9]{2}:[0-9]{2}:[0-9]{2}): (.*)\n\x00'
)

PORT = 9999
EVENTS = {
    re.compile(b'^World triggered "Round_Draw"'): 'round_draw',
    re.compile(b'^World triggered "Round_End"'): 'round_end',
    re.compile(b'^World triggered "Round_Start"'): 'round_start',
    re.compile(b'^Team "CT" triggered "CTs_Win" \(CT "(\d+)"\) \(T "(\d+)"\)'): 'team_cts_win_round',
    re.compile(b'^Team "TERRORIST" triggered "Terrorists_Win" \(CT "(\d+)"\) \(T "(\d+)"\)'): 'team_ts_win_round',
    re.compile(b'^Team "CT" scored "(\d+)" with "(\d+)" players$'): 'team_cts_win_game',
    re.compile(b'^Team "TERRORIST" scored "(\d+)" with "(\d+)" players$'): 'team_ts_win_game',
}


class LogEntry:

    def _parse_data(self, data):
        match = re.match(log_entry_regexp, data)
        if match:
            date, entry = match.groups()
            # logger.debug(entry)
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
            logger.info('Publishing event %s with data %s' % (event, groups))
            redis.publish('hlds_events', dill.dumps((event, groups)))


class DatagramProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        EventHandler().publish(data)


loop = asyncio.get_event_loop()
logger.info('Starting HLDS logging server on port %d' % PORT)

listen = loop.create_datagram_endpoint(
    DatagramProtocol,
    local_addr=('0.0.0.0', PORT)
)
transport, protocol = loop.run_until_complete(listen)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

transport.close()
loop.close()
