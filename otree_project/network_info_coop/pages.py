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
    def is_displayed(self):
        return self.round_number > 1

    def vars_for_template(self):
        prev_round = self.round_number - 1
        prev_p = self.player.in_round(prev_round)

        return dict(
            prev_round=prev_round,
            prev_contribution=prev_p.contribution,         # own only
            prev_payoff=prev_p.payoff,
            prev_cum_payoff=prev_p.cumulative_payoff(),    # cumulative up to prev_round
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

        payoff_rows = []
        for pl in g.get_players():
            payoff_rows.append(dict(
                pid=pl.id_in_group,
                is_you=(pl.id_in_group == p.id_in_group),
                payoff=pl.payoff
            ))

        return dict(
            your_contribution=p.contribution,          # still allowed: own contribution
            your_payoff=p.payoff,                      # payoff this round
            your_cum_payoff=p.cumulative_payoff(),      # cumulative payoff (incl this round)
            payoff_rows=payoff_rows,
        )


page_sequence = [
    Instructions,
    ReviewLastRound,
    ObserveSignals,
    Decide,
    ResultsWaitPage,
    Results,
]
