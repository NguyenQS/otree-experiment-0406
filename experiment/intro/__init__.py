from otree.api import *

class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    pass

class PageOne(Page):
    pass

class PageTwo(Page):
    pass

page_sequence = [PageOne, PageTwo]
