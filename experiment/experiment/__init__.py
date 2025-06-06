import random

from otree.api import *

doc = """
MATB-II und SSP kombiniert in einer App
"""

# === KONSTANTEN ===
class C(BaseConstants):
    NAME_IN_URL = 'experiment'
    PLAYERS_PER_GROUP = None
    #NUM_ROUNDS = 23  # 3 für MATB + 20 für SSP
    NUM_ROUNDS = 10
    SSP_START_ROUND = 4
    GRID_SIZE = 10

    FIXED_SSP_DIFFICULTY = [3, 4, 5, 4, 6, 5]  # z. B. für 6 SSP-Runden



# === SUBSESSION, GROUP, PLAYER ===
class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # MATB
    sysmon_score = models.IntegerField(min=0, max=100, blank=True)
    tracking_score = models.IntegerField(min=0, max=100, blank=True)
    comm_score = models.IntegerField(min=0, max=100, blank=True)
    resman_score = models.IntegerField(min=0, max=100, blank=True)

    # SSP
    sequence = models.LongStringField(blank=True)
    response = models.LongStringField(blank=True)
    correct = models.BooleanField(blank=True)
    difficulty = models.IntegerField(initial=3)
    max_span = models.IntegerField(initial=0)
    total_time_used = models.IntegerField(initial=0)

    timeout_seconds = models.IntegerField(initial=0)


    def generate_sequence(self):
        seq = random.sample(range(C.GRID_SIZE), self.difficulty)
        self.sequence = ','.join(map(str, seq))

    def update_difficulty(self):
        pass # nicht mehr benutzt


# === MATB PAGES ===
class MATB_Task(Page):
    form_model = 'player'
    form_fields = ['sysmon_score', 'tracking_score', 'comm_score', 'resman_score']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number <= 3

class MATB_Page(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3


# === SSP PAGES ===
class SSP_Task(Page):
    form_model = 'player'
    form_fields = ['response']

    @staticmethod
    def is_displayed(player: Player):
        return C.SSP_START_ROUND <= player.round_number < C.NUM_ROUNDS


    @staticmethod
    def get_timeout_seconds(player: Player):
        index = player.round_number - C.SSP_START_ROUND
        player.difficulty = C.FIXED_SSP_DIFFICULTY[index]
        return 30 if player.difficulty >= 6 else 15


    @staticmethod
    def before_render(player: Player):
        if player.round_number == C.SSP_START_ROUND and not player.sequence:
            player.generate_sequence()

    @staticmethod
    def vars_for_template(player: Player):
        index = player.round_number - C.SSP_START_ROUND
        player.difficulty = C.FIXED_SSP_DIFFICULTY[index]
        player.generate_sequence()
        return {
            'sequence': player.sequence,
            'difficulty': player.difficulty,
        }


    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        correct_seq = player.sequence.split(',')
        response_seq = player.response.split(',') if player.response else []
        player.correct = correct_seq == response_seq
        if player.correct:
            player.max_span = max(player.max_span, player.difficulty)
        # kein update_difficulty mehr nötig
        player.total_time_used = sum(p.timeout_seconds for p in player.in_all_rounds())



class SSP_Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        max_span = max(p.max_span for p in player.in_all_rounds())
        return {'max_span': max_span}


# === PAGE SEQUENCE ===
page_sequence = [
    MATB_Task,
    MATB_Page,
    SSP_Task,
    SSP_Results
] #+ [SSP_Task] * (C.NUM_ROUNDS - C.SSP_START_ROUND) + [SSP_Results]
