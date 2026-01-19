from otree.api import *
from .models import C


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return dict(
            network_type=self.group.network_type,
            n=C.PLAYERS_PER_GROUP,
            num_rounds=C.NUM_ROUNDS,
            endowment=C.ENDOWMENT,
            contrib_amt=C.CONTRIBUTION_AMOUNT,
            signal_accuracy=C.SIGNAL_ACCURACY,
            hub_is_player1=True,
        )


class ObserveSignals(Page):
    """
    Round timing:
      1) private signal
      2) observation (mechanical sharing)
      3) contribution + belief
    """
    def vars_for_template(self):
        p = self.player
        observed = p.signals_observed_this_round()

        return dict(
            network_type=self.group.network_type,
            observed_signals=observed,
            is_hub=p.is_hub(),  # IMPORTANT: required by ObserveSignals.html
        )


class Decide(Page):
    form_model = 'player'
    form_fields = ['contribute', 'belief']

    def vars_for_template(self):
        return dict(
            endowment=C.ENDOWMENT,
            contrib_amt=C.CONTRIBUTION_AMOUNT,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'compute_payoffs'


class Results(Page):
    def vars_for_template(self):
        p = self.player
        g = self.group
        return dict(
            contributed=p.contribute,
            contribution_amount=p.contribution_amount(),
            total_contribution=g.total_contribution,
            payoff=p.payoff,
            # Minimal feedback (no MPCR, no state, no histories)
        )


page_sequence = [
    Instructions,
    ObserveSignals,
    Decide,
    ResultsWaitPage,
    Results,
]
