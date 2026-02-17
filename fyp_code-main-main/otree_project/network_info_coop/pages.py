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
            mpcr_high=C.MPCR_HIGH,
            mpcr_low=C.MPCR_LOW,
        )


class Comprehension(Page):
    form_model = 'player'
    form_fields = ['cq_payoff', 'cq_mpcr', 'cq_state', 'cq_network', 'cq_belief']

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        # Always provide feedback + all keys so template never crashes
        fb = self.participant.vars.get('cq_feedback', {}) or {}
        for k in ['cq_payoff', 'cq_mpcr', 'cq_state', 'cq_network', 'cq_belief']:
            fb.setdefault(k, None)

        return dict(
            feedback=fb,
        )

    def error_message(self, values):
        # Answer key: field -> correct choice number + explanation
        key = {
            'cq_payoff': dict(correct=1, expl="Payoff = Endowment − your contribution + MPCR × (total group contribution)."),
            'cq_mpcr': dict(correct=3, expl="MPCR depends on the hidden HIGH/LOW state chosen at the start, not on choices or belief."),
            'cq_state': dict(correct=2, expl="The hidden state is fixed for all rounds once chosen."),
            'cq_network': dict(correct=3, expl="You observe your own signal and only the signals of players you are connected to."),
            'cq_belief': dict(correct=4, expl="Belief is recorded for research but does not affect payoffs and is not shared."),
        }

        feedback = {}
        any_wrong = False

        for field, meta in key.items():
            chosen = values.get(field)
            if chosen != meta['correct']:
                any_wrong = True
                feedback[field] = dict(
                    chosen=chosen,
                    correct=meta['correct'],
                    expl=meta['expl'],
                )

        # Ensure all keys exist (template safety)
        for k in key.keys():
            feedback.setdefault(k, None)

        self.participant.vars['cq_feedback'] = feedback

        if any_wrong:
            return "Some answers were incorrect. The correct answers and explanations are shown below. Please try again."

        # If all correct, clear feedback so nothing shows anymore
        self.participant.vars.pop('cq_feedback', None)



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
            signals_history=p.signals_history(),
            pid=p.id_in_group,
            hub_id=self.group.hub_id,  # ✅ add for dynamic network diagram
        )


class Decide(Page):
    form_model = 'player'
    form_fields = ['contribution', 'belief']
    timeout_seconds = 60

    def vars_for_template(self):
        b = self.player.field_maybe_none('belief')
        belief_value = 50 if b is None else b

        contrib_history_all = []
        last_completed_round = self.round_number - 1

        for r in range(1, last_completed_round + 1):
            gr = self.group.in_round(r)
            rows = []
            for pl in gr.get_players():
                pr = pl.in_round(r)
                rows.append(dict(
                    pid=pr.id_in_group,
                    is_you=(pr.id_in_group == self.player.id_in_group),
                    contribution=pr.field_maybe_none('contribution'),
                ))
            contrib_history_all.append(dict(round=r, rows=rows))

        return dict(
            signals_history=self.player.signals_history(),
            contrib_history_all=contrib_history_all,
            pid=self.player.id_in_group,
            network_type=self.group.network_type,
            endowment=C.ENDOWMENT,
            min_contrib=C.MIN_CONTRIBUTION,
            max_contrib=C.MAX_CONTRIBUTION,
            belief_value=belief_value,
        )

    
    def before_next_page(self, timeout_happened=False):
        if timeout_happened:
            if self.player.field_maybe_none('belief') is None:
                self.player.belief = 50
            if self.player.field_maybe_none('contribution') is None:
                self.player.contribution = C.MIN_CONTRIBUTION




class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'compute_payoffs'


class Results(Page):
    def vars_for_template(self):
        p = self.player
        g = self.group

        contribution_rows = []
        for pl in g.get_players():
            contribution_rows.append(dict(
                pid=pl.id_in_group,
                is_you=(pl.id_in_group == p.id_in_group),
                contribution=pl.contribution
            ))

        return dict(
            your_contribution=p.contribution,
            your_payoff=p.payoff,
            your_cum_payoff=p.cumulative_payoff(),
            contribution_rows=contribution_rows,
        )

class End(Page):
    """Shown only after the final round."""
    
    def is_displayed(self):
        return self.round_number == C.NUM_ROUNDS


page_sequence = [
    Instructions,
    Comprehension,
    ObserveSignals,
    Decide,
    ResultsWaitPage,
    Results,
    End,
]
