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
    NUM_ROUNDS = 90
    GRID_SIZE = 10
    SSP_START_ROUND = 3
    #FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4]  # die Sequenz wird insgesamt viermal gespielt, siehe unten
    FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4, 3, 4, 5, 7, 6, 5, 6, 5, 4, 3, 4, 5, 7, 6, 5, 6, 5, 4]  # ggf. kürzen oder anpassen
    MATB_ROUNDS = [14, 15, 29, 30, 44, 45, 59, 60, 74, 75, 89, 90]
    MATB_LEVEL_SEQUENCE = ['level1', 'level2', 'level3', 'level1', 'level2',
                           'level3', 'level1', 'level2', 'level3', 'level1',
                           'level2', 'level3']



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
    nback_data_json = models.LongStringField()

    total_correct = models.IntegerField()
    mean_rt = models.FloatField()



    # SSP
    sequence = models.LongStringField(blank=True)
    response = models.LongStringField(blank=True)
    correct = models.BooleanField(blank=True)
    difficulty = models.IntegerField(initial=3)
    max_span = models.IntegerField(initial=0)
    total_time_used = models.IntegerField(initial=0)
    timeout_seconds = models.IntegerField(initial=0)

    first_error_index = models.IntegerField(blank=True, null=True)  # Index des ersten Fehlers

    def generate_sequence(self):
        seq = random.sample(range(C.GRID_SIZE), self.difficulty)
        self.sequence = ','.join(map(str, seq))

    @staticmethod
    def current_letter(player: 'Player'):
        return N_BACK_STIMULI[player.round_number - 1]

    @staticmethod
    def target_letter(player: 'Player'):
        if player.round_number <= 12:
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
    NBACK_ROUNDS = [13, 28, 43, 58, 73, 88]

    @staticmethod
    def is_displayed(player):
        return player.round_number in NBackBatch.NBACK_ROUNDS

    @staticmethod
    def vars_for_template(player):
        n_trials = 5
        n_back = 2
        num_targets = 1
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


    @staticmethod
    def before_next_page(player, timeout_happened):
        import json
        trials = json.loads(player.nback_data_json)
        correct = [t for t in trials if t['correct']]
        reaction_times = [t['reaction_time'] for t in trials if t['reaction_time'] is not None]

        player.total_correct = len(correct)
        player.mean_rt = sum(reaction_times) / len(reaction_times) if reaction_times else None



# --- SSP ---
class SSP_Task(Page):
    form_model = 'player'
    form_fields = ['response']

    SSP_ROUNDS = list(range(3, 12)) + list(range(18, 27)) + list(range(33, 42)) + list(range(48, 57)) + list(range(63, 72)) + list(range(78, 87))

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
        correct_seq = player.sequence.split(',')  # z. B. ['3','1','4']
        response_seq = player.response.split(',') if player.response else []

        # Speichere die Sequenzen für die CSV
        player.sequence = ','.join(correct_seq)
        player.response = ','.join(response_seq)

        # Überprüfen, ob korrekt
        is_correct = correct_seq == response_seq
        player.correct = is_correct

        # Fehlerindex berechnen
        first_error = -1
        for i, (c, r) in enumerate(zip(correct_seq, response_seq)):
            if c != r:
                first_error = i
                break
        if len(response_seq) < len(correct_seq):
            first_error = len(response_seq)

        player.first_error_index = -1 if is_correct else first_error

        # Max-Span aktualisieren
        if player.correct:
            player.max_span = max(player.max_span, player.difficulty)

        # Gesamtzeit aufsummieren
        player.total_time_used = sum(p.timeout_seconds for p in player.in_all_rounds())




class SSP_Results(Page):
    SSP_BLOCKS = [
        range(3, 12),   # Block 1
        range(18, 27),  # Block 2
        range(33, 42),  # Block 3
        range(48, 57),  # Block 4
        range(63, 72),  # Block 5
        range(78, 87),  # Block 6
    ]

    @staticmethod
    def is_displayed(player: Player):
        # Am Ende jedes Blocks anzeigen (nach letzter Runde des Blocks)
        return player.round_number in [12, 27, 42, 57, 72, 87]

    @staticmethod
    def vars_for_template(player: Player):
        current_round = player.round_number
        for block in SSP_Results.SSP_BLOCKS:
            if current_round == block.stop:
                block_players = player.in_rounds(block.start, block.stop - 1)
                # Nur richtige Antworten zählen
                correct_trials = [p for p in block_players if p.correct]
                if correct_trials:
                    max_span = max(p.difficulty for p in correct_trials)
                else:
                    max_span = 0
                return {'max_span': max_span}
        return {'max_span': 0}  # Fallback



class StartPage(Page):
    form_model = 'player'  

    @staticmethod
    def is_displayed(player):
        return player.round_number in [1, 16, 31, 46, 61, 76]


class CrossPage(Page):
    form_model = 'player'  

    @staticmethod
    def is_displayed(player):
        return player.round_number in [2, 17, 32, 47, 62, 77]




# === SEQUENCE ===
page_sequence = [
    StartPage,
    CrossPage,
    SSP_Task,
    SSP_Results,
    NBackBatch,
    MATB_Task
]
