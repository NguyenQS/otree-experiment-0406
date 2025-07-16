import json
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
    NUM_ROUNDS = 108
    GRID_SIZE = 10
    SSP_START_ROUND = 3
    #FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4]  # die Sequenz wird insgesamt sechsmal gespielt, siehe unten
    FIXED_SSP_DIFFICULTY = [3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4,3, 4, 5, 7, 6, 5, 6, 5, 4, 3, 4, 5, 7, 6, 5, 6, 5, 4, 3, 4, 5, 7, 6, 5, 6, 5, 4]  
    MATB_ROUNDS = [17, 18, 35, 36, 53, 54, 71, 72, 89, 90, 107, 108]
    MATB_LEVEL_SEQUENCE = ['level1', 'level2', 'level3', 'level1', 'level2',
                           'level3', 'level1', 'level2', 'level3', 'level1',
                           'level2', 'level3']

    # neu
    # Stroop
    COGNITIVE_TEST_DURATION = 30
    STROOP_WORDS = ['red', 'blue', 'green', 'yellow']
    STROOP_COLORS = ['#ff0000', '#0000ff', '#00ff00', '#ffff00']



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

    
    # neu
    # var for Multidimensional Fatigue Inventory (MFI)
    mfi_1 = models.IntegerField(widget=widgets.RadioSelect, choices=[-3, -2, -1, 0, 1, 2, 3])  # When I am doing something, I can keep my thoughts on it.
    mfi_2 = models.IntegerField(widget=widgets.RadioSelect, choices=[-3, -2, -1, 0, 1, 2, 3])  # I can concentrate well.
    mfi_3 = models.IntegerField(widget=widgets.RadioSelect, choices=[-3, -2, -1, 0, 1, 2, 3])  # It takes a lot of effort to concentrate on things.
    mfi_4 = models.IntegerField(widget=widgets.RadioSelect, choices=[-3, -2, -1, 0, 1, 2, 3])  # My thoughts easily wander.

    # var for Visual Analogous Scales
    mental_fatigue = models.IntegerField(min=1, max=100)
    motivation = models.IntegerField(min=1, max=100)
    mental_workload = models.IntegerField(min=1, max=100)
    frustration = models.IntegerField(min=1, max=100 )

    # var for reaction time task and for sustained attention to respond task
    timings_json = models.LongStringField(blank=True, null=True)

    # var for stroop
    cognitive_test_score = models.IntegerField(
        initial=0,
        doc="Score on cognitive load test (correct answers)"
    )

    cognitive_test_reaction_time = models.FloatField(
        initial=0.0,
        doc="Average reaction time in cognitive test (milliseconds)"
    )

    cognitive_test_errors = models.IntegerField(
        initial=0,
        doc="Number of errors in cognitive test"
    )

    # SART Test Results
    sart_correct_responses = models.IntegerField(initial=0)
    sart_errors = models.IntegerField(initial=0)
    sart_avg_reaction_time = models.FloatField(initial=0.0)




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
    NBACK_ROUNDS = [16, 34, 52, 70, 88, 106]

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

    SSP_ROUNDS = list(range(6, 15)) + list(range(24, 33)) + list(range(42, 51)) + list(range(60, 69)) + list(range(78, 87)) + list(range(96, 105))

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
        range(6, 15),   # Block 1
        range(24, 33),  # Block 2
        range(42, 51),  # Block 3
        range(60, 69),  # Block 4
        range(78, 87),  # Block 5
        range(96, 105),  # Block 6
    ]

    @staticmethod
    def is_displayed(player: Player):
        # Am Ende jedes Blocks anzeigen (nach letzter Runde des Blocks)
        return player.round_number in [15, 33, 51, 69, 87, 105]

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
        return player.round_number in [1, 19, 37, 55, 73, 91]


class CrossPage(Page):

    form_model = 'player'  

    @staticmethod
    def is_displayed(player):
        return player.round_number in [2, 20, 38, 56, 74, 92]



'''
class Fragebogen(Page):

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [3, 21, 39, 57, 75, 93]


class SART(Page):

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [4, 22, 40, 58, 76, 94]


class ReactionTime(Page):

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [5, 23, 41, 59, 77, 95]

'''



# -- folgender Code von anderen Studenten -------------------------------------------------------------------

class VASPage(Page):
    """
    Viusal Analogous Scales for fatigue, motivation, workload frustration
    Quick and Dirty Solution - Instructions not validated
    """
    form_model = 'player'
    form_fields = ['mental_fatigue', 'motivation', 'mental_workload', 'frustration']

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [3, 21, 39, 57, 75, 93]


class MentalFatigueInventory(Page): # TODO: könnnen wir das auch einmal mitten drin (nach der hälfte) und am ende fragen?
    """
    Using the Multidimensional Mental Fatigue Inventory - Subscale

    Smets, E. M. A., Garssen, B., Bonke, B. D., & De Haes, J. C. J. M. (1995).
    The Multidimensional Fatigue Inventory (MFI) psychometric qualities of an instrument to assess fatigue.
    Journal of psychosomatic research, 39(3), 315-325.
    """

    form_model = 'player'
    form_fields = ['mfi_1', 'mfi_2', 'mfi_3', 'mfi_4']

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [3, 57, 93]


# Code provided by Dary
class ReactionTime(Page):
    @staticmethod
    def live_method(player: Player, data):
        idx = str(data.get('trial_index'))
        rt = data.get('reaction_time')

        if idx is None or rt is None:
            return

        raw = player.field_maybe_none('timings_json')
        try:
            existing = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            existing = {}

        if idx not in existing:
            existing[idx] = {}

        existing[idx]['reaction_time'] = rt
        player.timings_json = json.dumps(existing)

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [5, 23, 41, 59, 77, 95]

class ReactionTimeMT(Page):

    form_model = 'player'

    timeout_seconds = 60 * 2

    @staticmethod
    def live_method(player: Player, data):
        rt = data.get('response_time')
        reactionT = data.get('leave_time')
        idx = str(data.get('trial_index'))


        if idx is None:
            return  {player.id_in_group: {'error': 'Missing trial_index'}} # must have trial index

        raw = player.field_maybe_none('timings_json')
        try:
            existing = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            existing = {}

        # Initialize if not present
        if idx not in existing:
            existing[idx] = {}

        if rt is not None:
            existing[idx]["response_time"] = rt
        if reactionT is not None:
            existing[idx]["reaction_time"] = reactionT

        player.timings_json = json.dumps(existing)

    @staticmethod
    def is_displayed(player):
        return player.round_number in [5, 23, 41, 59, 77, 95]



# Code provided by Dary
class Sart(Page):
    @staticmethod
    def live_method(player: Player, data):
        idx = str(data.get('trial_index'))
        rt = data.get('reaction_time')
        correct = data.get('is_correct')

        if idx is None:
            return

        raw = player.field_maybe_none('timings_json')
        try:
            existing = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            existing = {}

        existing[idx] = {
            'reaction_time': rt,
            'is_correct': correct,
        }

        player.timings_json = json.dumps(existing)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        raw = player.field_maybe_none('timings_json')

        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {}

        total_rt = 0
        rt_count = 0
        correct = 0
        errors = 0

        for trial in data.values():
            is_correct = trial.get('is_correct')
            rt = trial.get('reaction_time')

            if is_correct:
                correct += 1
                if rt:
                    try:
                        total_rt += float(rt)
                        rt_count += 1
                    except ValueError:
                        pass
            else:
                errors += 1

        player.sart_correct_responses = correct
        player.sart_errors = errors
        player.sart_avg_reaction_time = round(total_rt / rt_count, 2) if rt_count > 0 else 0.0

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [4, 22, 40, 58, 76, 94]

# Code provided by Till (original oTree 3)
class StroopInstruction(Page):
    timeout_seconds = 20

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return {
            'session_number': player.round_number
        }

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [4, 22, 40, 58, 76, 94]

# Code provided by Till
class Stroop(Page):
    form_model = 'player'
    form_fields = ['cognitive_test_score', 'cognitive_test_reaction_time', 'cognitive_test_errors']
    timeout_seconds = 30

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        # Generate random Stroop test items for baseline
        test_items = []
        color_mapping = {
            '#ff0000': 'red',
            '#0000ff': 'blue',
            '#00ff00': 'green',
            '#ffff00': 'yellow'
        }

        for i in range(20):  # 20 items
            word = random.choice(C.STROOP_WORDS)
            color_hex = random.choice(C.STROOP_COLORS)
            color_name = color_mapping[color_hex]

            test_items.append({
                'word': word,
                'color': color_hex,
                'correct_answer': color_name
            })

        return {
            'test_items': test_items,
            'test_duration': 30,
            'session_number': player.round_number
        }

    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number in [4, 22, 40, 58, 76, 94]


# Code provided by Till
class StroopResults(Page):
    timeout_seconds = 20

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return {
            'session_number': player.round_number,
            'score': player.cognitive_test_score or 0,
            'reaction_time': player.cognitive_test_reaction_time or 0,
            'errors': player.cognitive_test_errors or 0,
            'total_items': 20
        }

    form_model = 'player'
    form_fields = ['cognitive_test_score', 'cognitive_test_errors', 'cognitive_test_reaction_time']

    @staticmethod
    def is_displayed(player):
        return player.round_number in [4, 22, 40, 58, 76, 94]



# === SEQUENCE ===

page_sequence = [
    StartPage,
    CrossPage,
    MentalFatigueInventory,
    VASPage,
    StroopInstruction,
    Stroop,
    StroopResults,
    ReactionTimeMT,
    SSP_Task,
    SSP_Results,
    NBackBatch,
    MATB_Task
]



