from otree.api import *
import json

class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

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

        if idx not in existing:
            existing[idx] = {}

        if rt is not None:
            existing[idx]['reaction_time'] = rt
        existing[idx]['is_correct'] = correct

        player.timings_json = json.dumps(existing)

class PageOne(Page):
    pass

class PageTwo(Page):
    pass

page_sequence = [
    # PageOne,
    # PageTwo,
    MentalFatigueInventory,
    VASPage,
    Sart,
    ReactionTime,
]
