import random
import string

from otree.api import *

doc = """
MATB-II, N-Back und SSP kombiniert in einer App
"""


# === KONSTANTEN ===
class C(BaseConstants):
    NAME_IN_URL = 'experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 55  
    MATB_ROUNDS = [1, 2, 14, 15, 27, 28, 40, 41, 53, 54]
    MATB_LEVEL_SEQUENCE = ['level1', 'level2', 'level3', 'level1', 'level2',
                           'level3', 'level1', 'level2', 'level3', 'level1']
    GRID_SIZE = 10
    SSP_START_ROUND = 6
    #FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4]  # die Sequenz wird insgesamt viermal gespielt, siehe unten
    FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4]  # ggf. kürzen oder anpassen


# Erst hier definieren, nachdem C.NUM_ROUNDS existiert
VOWELS = set("AEIOU")
ALLOWED_LETTERS = [letter for letter in string.ascii_uppercase if letter not in VOWELS]
N_BACK_STIMULI = [random.choice(ALLOWED_LETTERS) for _ in range(60)]


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
    nback_data_json = models.LongStringField(blank=True)


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
        return player.round_number in C.MATB_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        index = C.MATB_ROUNDS.index(player.round_number)
        level = C.MATB_LEVEL_SEQUENCE[index]
        return {'matb_level': level}



# --- N-BACK ---

class NBackBatch(Page):
    form_model = 'player'
    form_fields = ['nback_data_json']

    # Runden, in denen der N-Back gezeigt werden soll
    NBACK_ROUNDS = [3, 16, 29, 42, 55]

    @staticmethod
    def is_displayed(player):
        return player.round_number in NBackBatch.NBACK_ROUNDS

    @staticmethod
    def vars_for_template(player):
        n_trials = 60
        n_back = 2
        num_targets = 8
        letters = ALLOWED_LETTERS  # z.B. nur Konsonanten

        stimuli = [random.choice(letters) for _ in range(n_back)]  # Erste 2 Buchstaben zufällig

        # Zufällige Positionen für Treffer (ohne Duplikate)
        target_positions = random.sample(range(n_back, n_trials), num_targets)

        for i in range(n_back, n_trials):
            if i in target_positions:
                # Treffer: Buchstabe von vor 2 Positionen übernehmen
                stimuli.append(stimuli[i - n_back])
            else:
                # Kein Treffer: Buchstabe anders als der von vor 2 Positionen
                choices = [l for l in letters if l != stimuli[i - n_back]]
                stimuli.append(random.choice(choices))

        targets = []
        for i in range(n_trials):
            if i < n_back:
                targets.append(False)
            else:
                targets.append(stimuli[i] == stimuli[i - n_back])

        return dict(stimuli=stimuli, targets=targets, n_back=n_back)




# --- SSP ---
class SSP_Task(Page):
    form_model = 'player'
    form_fields = ['response']

    SSP_ROUNDS = list(range(4, 13)) + list(range(17, 26)) + list(range(30, 39)) + list(range(43, 52))

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in SSP_Task.SSP_ROUNDS

    @staticmethod
    def get_timeout_seconds(player: Player):
        index = SSP_Task.SSP_ROUNDS.index(player.round_number)
        player.difficulty = C.FIXED_SSP_DIFFICULTY[index]
        return 20 if player.difficulty >= 6 else 10

    @staticmethod
    def before_render(player: Player):
        if not player.sequence:
            player.generate_sequence()

    @staticmethod
    def vars_for_template(player: Player):
        index = SSP_Task.SSP_ROUNDS.index(player.round_number)
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
    SSP_BLOCKS = [
        range(4, 13),   # Block 1
        range(17, 26),  # Block 2
        range(30, 39),  # Block 3
        range(43, 52),  # Block 4
    ]

    @staticmethod
    def is_displayed(player: Player):
        # Am Ende jedes Blocks anzeigen (nach letzter Runde des Blocks)
        return player.round_number in [13, 26, 39, 52]

    @staticmethod
    def vars_for_template(player: Player):
        current_round = player.round_number
        for block in SSP_Results.SSP_BLOCKS:
            if current_round == block.stop:
                block_players = [p for p in player.in_rounds(block.start, block.stop - 1)]
                max_span = max(p.max_span for p in block_players)
                return {'max_span': max_span}
        return {'max_span': 0}  # Fallback



# === SEQUENCE ===
page_sequence = [
    MATB_Task,
    NBackBatch,
    SSP_Task,
    SSP_Results,
]
