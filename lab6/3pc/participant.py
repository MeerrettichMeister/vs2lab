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
        self.coordinator = {}
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

    def fallback(self, decision):
        # Help any other participant when coordinator crashed
        num_of_others = len(self.all_participants) - 1
        while num_of_others > 0:
            num_of_others -= 1
            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 2)
            if msg and msg[1] == NEED_DECISION:
                self.channel.send_to({msg[0]}, decision)

        return "Participant {} terminated in state {} due to {}.".format(
            self.participant, self.state, decision)


    def run(self):
        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        if not msg:  # Crashed coordinator - give up entirely
            # decide to locally abort (before doing anything)
            decision = LOCAL_ABORT
            self._enter_state('ABORT')
            return self.fallback(decision)

        assert msg[1] == VOTE_REQUEST
        # Firstly, come to a local decision
        decision = self._do_work()  # proceed with local activities

        # If local decision is negative,
        # then vote for abort and quit directly
        if decision == LOCAL_ABORT:
            self.channel.send_to(self.coordinator, VOTE_ABORT)
            self._enter_state('ABORT')
            return self.fallback(decision)
        # If local decision is positive,
        # we are ready to proceed the joint commit
        assert decision == LOCAL_SUCCESS
        self._enter_state('READY')
        self.channel.send_to(self.coordinator, VOTE_COMMIT)
        # Wait for coordinator precommit or abort
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed coordinator
            return self.fallback(decision)

        decision = msg[1]
        if decision == GLOBAL_ABORT:
            self._enter_state('ABORT')
            return self.fallback(decision)
        assert decision == PREPARE_COMMIT
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.coordinator, READY_COMMIT)

        # Wait for coordinator global commit or abort
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg:  # Crashed coordinator
            return self.fallback(decision)

        decision = msg[1]
        if decision == GLOBAL_COMMIT:
            self._enter_state('COMMIT')

        return self.fallback(decision)
