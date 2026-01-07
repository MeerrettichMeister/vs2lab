import random
import logging

# coordinator messages
from const3PC import VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decissions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT, PREPARE_COMMIT, READY_COMMIT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, NEED_DECISION
# misc constants
from const3PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a two phase commit participant.
    - state written to stable log (but recovery is not considered)
    - in case of coordinator crash, participants mutually synchronize states
    - system blocks if all participants vote commit and coordinator crashes
    - allows for partially synchronous behavior with fail-noisy crashes
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.2pc.Participant")
        self.coordinator = set()
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 2 / 3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')  # Start in local INIT state.

    def _synchronize(self):
        designated_replacement = min(self.all_participants)

        if self.participant == designated_replacement:
            # Pk READY or ABORT corresponds to C WAIT, so global abort
            if self.state == 'READY' or self.state == 'ABORT':
                self._enter_state('ABORT')
                self.channel.send_to(self.all_participants, GLOBAL_ABORT)
            elif self.state == 'PRECOMMIT':
                self._enter_state('COMMIT')
                self.channel.send_to(self.all_participants, GLOBAL_COMMIT)
            elif self.state == 'COMMIT': # or self.state == 'ABORT':
                # everyone should already be here
                pass

        else:
            self.coordinator.add(designated_replacement)
            msg = self.channel.receive_from(self.coordinator, TIMEOUT)

            if msg[1] == GLOBAL_ABORT:
                self._enter_state('ABORT')
            elif msg[1] == GLOBAL_COMMIT:
                if self.state in ['READY', 'PRECOMMIT', 'COMMIT']:
                    self._enter_state('COMMIT')
                else:
                    # cannot transition from other state
                    pass

    def run(self):
        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        # Crashed coordinator - give up entirely
        if not msg:
            # early exit, no synchronization necessary
            decision = LOCAL_ABORT
            self._enter_state('ABORT')
            return "Participant {} terminated in state {} due to {}.".format(self.participant, self.state, decision)

        assert msg[1] == VOTE_REQUEST
        # await local result
        decision = self._do_work()

        # If local decision is negative, then vote for abort
        if decision == LOCAL_ABORT:
            self.channel.send_to(self.coordinator, VOTE_ABORT)
            self._enter_state('ABORT')
        elif decision == LOCAL_SUCCESS:
            self.channel.send_to(self.coordinator, VOTE_COMMIT)
            self._enter_state('READY')

        # await for coordinator precommit or abort
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        # Crashed coordinator
        if not msg:
            # after sync, we are all either COMMIT or ABORT
            self._synchronize()
            return "Participant {} synchronized and terminated in state {}".format(self.participant, self.state)

        decision = msg[1]
        if decision == GLOBAL_ABORT:
            self._enter_state('ABORT')
            return "Participant {} terminated in state {} due to {}".format(self.participant, self.state, decision)

        assert decision == PREPARE_COMMIT
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.coordinator, READY_COMMIT)

        # Wait for coordinator global commit or abort
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed
            self._synchronize()
            return "Participant {} synchronized and terminated in state {}".format(self.participant, self.state)

        decision = msg[1]
        assert decision == GLOBAL_COMMIT
        self._enter_state('COMMIT')
        return "Participant {} terminated in state {} due to {}".format(self.participant, self.state, decision)
