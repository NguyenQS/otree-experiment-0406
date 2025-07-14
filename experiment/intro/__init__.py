from otree.api import *
import json
import random

class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # Stroop
    COGNITIVE_TEST_DURATION = 30
    STROOP_WORDS = ['red', 'blue', 'green', 'yellow']
    STROOP_COLORS = ['#ff0000', '#0000ff', '#00ff00', '#ffff00']

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
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


class VASPage(Page):
    """
    Viusal Analogous Scales for fatigue, motivation, workload frustration
    Quick and Dirty Solution - Instructions not validated
    """
    form_model = 'player'
    form_fields = ['mental_fatigue', 'motivation', 'mental_workload', 'frustration']


class MentalFatigueInventory(Page): # TODO: könnnen wir das auch einmal mitten drin (nach der hälfte) und am ende fragen?
    """
    Using the Multidimensional Mental Fatigue Inventory - Subscale

    Smets, E. M. A., Garssen, B., Bonke, B. D., & De Haes, J. C. J. M. (1995).
    The Multidimensional Fatigue Inventory (MFI) psychometric qualities of an instrument to assess fatigue.
    Journal of psychosomatic research, 39(3), 315-325.
    """

    form_model = 'player'
    form_fields = ['mfi_1', 'mfi_2', 'mfi_3', 'mfi_4']


# Code provided by Dary
class ReactionTimeMT(Page):
    timeout_seconds = 60 * 2

    @staticmethod
    def live_method(player: Player, data):
        rt = data.get('response_time')
        reactionT = data.get('leave_time')
        idx = str(data.get('trial_index'))

        if idx is None:
            return  # must have trial index

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


# Sustained Attenion to Response Task - not functional
# class Sart(Page):
#     @staticmethod
#     def live_method(player: Player, data):
#         idx = str(data.get('trial_index'))
#         rt = data.get('reaction_time')
#         correct = data.get('is_correct')
#
#         if idx is None:
#             return
#
#         raw = player.field_maybe_none('timings_json')
#         try:
#             existing = json.loads(raw) if raw else {}
#         except json.JSONDecodeError:
#             existing = {}
#
#         if idx not in existing:
#             existing[idx] = {}
#
#         if rt is not None:
#             existing[idx]['reaction_time'] = rt
#         existing[idx]['is_correct'] = correct
#
#         player.timings_json = json.dumps(existing)



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

class PageOne(Page):
    pass

class PageTwo(Page):
    pass

page_sequence = [
    # PageOne,
    # PageTwo,
    MentalFatigueInventory,
    VASPage,
    StroopInstruction,
    Stroop,
    StroopResults,
    ReactionTimeMT,
]
