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
            min_contrib=C.MIN_CONTRIBUTION,
            max_contrib=C.MAX_CONTRIBUTION,
            signal_accuracy=C.SIGNAL_ACCURACY,
        )


class ReviewLastRound(Page):
    """
    Shows private feedback from the previous round at the START of each new round.
    Displayed from Round 2 onward.
    """
    def is_displayed(self):
        return self.round_number > 1

    def vars_for_template(self):
        prev_p = self.player.in_round(self.round_number - 1)
        prev_g = self.group.in_round(self.round_number - 1)

        return dict(
            prev_round=self.round_number - 1,
            prev_contribution=prev_p.contribution,
            prev_payoff=prev_p.payoff,
            prev_total_contribution=prev_g.total_contribution,  # optional
        )


class ObserveSignals(Page):
    """
    Round timing:
      0) (Round>=2) review last round
      1) private signal drawn by system
      2) observation (mechanical sharing)
      3) contribution + belief
    """
    def vars_for_template(self):
        p = self.player
        observed = p.signals_observed_this_round()
        return dict(
            network_type=self.group.network_type,
            observed_signals=observed,
            is_hub=p.is_hub(),
        )


class Decide(Page):
    form_model = 'player'
    form_fields = ['contribution', 'belief']

    def vars_for_template(self):
        return dict(
            endowment=C.ENDOWMENT,
            min_contrib=C.MIN_CONTRIBUTION,
            max_contrib=C.MAX_CONTRIBUTION,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'compute_payoffs'


class Results(Page):
    def vars_for_template(self):
        p = self.player
        g = self.group

        contrib_rows = []
        for pl in g.get_players():
            contrib_rows.append(dict(
                pid=pl.id_in_group,
                is_you=(pl.id_in_group == p.id_in_group),
                contrib=pl.contribution
            ))

        return dict(
            your_contribution=p.contribution,
            total_contribution=g.total_contribution,
            payoff=p.payoff,
            contrib_rows=contrib_rows,
        )


page_sequence = [
    Instructions,
    ReviewLastRound,
    ObserveSignals,
    Decide,
    ResultsWaitPage,
    Results,
]
