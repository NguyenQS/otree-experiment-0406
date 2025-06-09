import random
import string

from otree.api import *

doc = """
MATB-II, N-Back und SSP kombiniert in einer App
"""

# === GLOBALE KONSTANTEN ===
#ALLOWED_LETTERS = list(string.ascii_uppercase[:10])  # A–J
#N_BACK_STIMULI = [random.choice(ALLOWED_LETTERS) for _ in range(C.NUM_ROUNDS)]

# === KONSTANTEN ===
class C(BaseConstants):
    NAME_IN_URL = 'experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 52  # z. B. 3 MATB + 10 N-Back + 9 SSP
    GRID_SIZE = 10
    SSP_START_ROUND = 44
    FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4]  # ggf. kürzen oder anpassen

# Erst hier definieren, nachdem C.NUM_ROUNDS existiert
ALLOWED_LETTERS = list(string.ascii_uppercase[:10])
N_BACK_STIMULI = [random.choice(ALLOWED_LETTERS) for _ in range(C.NUM_ROUNDS)]


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

    # N-Back
    reaction_time = models.FloatField(blank=True)
    clicked = models.BooleanField(blank=True)
    is_correct = models.BooleanField(blank=True)

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

    @staticmethod
    def current_letter(player: 'Player'):
        return N_BACK_STIMULI[player.round_number - 1]

    @staticmethod
    def target_letter(player: 'Player'):
        if player.round_number <= 2:
            return None
        return N_BACK_STIMULI[player.round_number - 3]

# === PAGES ===

# --- MATB ---
class MATB_Task(Page):
    form_model = 'player'
    form_fields = ['sysmon_score', 'tracking_score', 'comm_score', 'resman_score']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in [1, 2, 3]


'''
class MATB_Page(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3
'''

# --- N-BACK ---
class NBack(Page):
    form_model = 'player'
    form_fields = ['reaction_time', 'clicked']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in range(4, 44)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        current = Player.current_letter(player)
        target = Player.target_letter(player)
        if player.clicked is not None and target is not None:
            player.is_correct = player.clicked and (current == target)
        else:
            player.is_correct = False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'letter': Player.current_letter(player),
            'target': Player.target_letter(player),
        }

# --- SSP ---
class SSP_Task(Page):
    form_model = 'player'
    form_fields = ['response']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in range(44, 53)

    @staticmethod
    def get_timeout_seconds(player: Player):
        index = player.round_number - C.SSP_START_ROUND
        player.difficulty = C.FIXED_SSP_DIFFICULTY[index]
        return 20 if player.difficulty >= 6 else 10

    @staticmethod
    def before_render(player: Player):
        if not player.sequence:
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
        player.total_time_used = sum(p.timeout_seconds for p in player.in_all_rounds())

class SSP_Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 52

    @staticmethod
    def vars_for_template(player: Player):
        max_span = max(p.max_span for p in player.in_all_rounds())
        return {'max_span': max_span}

# === SEQUENCE ===
page_sequence = [
    MATB_Task,
    NBack,
    SSP_Task,
    SSP_Results,
]
