from otree.api import *
import random

doc = """
Network Information & Cooperation:
- Fixed hidden state (HIGH/LOW) across rounds
- Per-round noisy private signals
- Mechanical signal sharing via static network (hub-spoke vs ring)
- Repeated public goods game (binary contribution)
- Non-incentivized belief elicitation (not shared)
"""


class C(BaseConstants):
    NAME_IN_URL = 'network_info_coop'
    PLAYERS_PER_GROUP = 8
    NUM_ROUNDS = 15

    # Public goods
    ENDOWMENT = cu(20)
    CONTRIBUTION_AMOUNT = cu(10)

    # Unknown MPCR depends on state (held constant across treatments)
    MPCR_HIGH = 0.70
    MPCR_LOW = 0.30

    # Hidden state + signals
    STATE_HIGH = "HIGH"
    STATE_LOW = "LOW"
    SIGNAL_ACCURACY = 0.70  # P(signal = true_state)

    # Prior
    PRIOR_HIGH = 0.5


class Subsession(BaseSubsession):
    def creating_session(self):
        for g in self.get_groups():

            # Treatment assignment
            g.network_type = (self.session.config.get('network_type', 'ring') or 'ring').strip().lower()
            if g.network_type not in ('ring', 'hub'):
                g.network_type = 'ring'

            # Fixed hidden state
            if self.round_number == 1:
                g.state = random.choice([C.STATE_HIGH, C.STATE_LOW])
            else:
                g.state = g.in_round(1).state

            g.mpcr = C.MPCR_HIGH if g.state == C.STATE_HIGH else C.MPCR_LOW

            # Draw private signals
            for p in g.get_players():
                p.signal = p.draw_noisy_signal(
                    true_state=g.state,
                    accuracy=C.SIGNAL_ACCURACY
                )

            # 🔁 Hub updates posterior AFTER signals are drawn
            g.update_hub_posterior()


class Group(BaseGroup):
    network_type = models.StringField()
    state = models.StringField()
    mpcr = models.FloatField()

    total_contribution = models.CurrencyField(initial=0)

    # 🔊 Hub broadcasted posterior
    hub_posterior = models.FloatField(initial=C.PRIOR_HIGH)

    def hub_player(self):
        # Hub fixed as player 1
        return self.get_player_by_id(1)

    def update_hub_posterior(self):
        if self.network_type != 'hub':
            return

        q = C.SIGNAL_ACCURACY

        # Prior
        if self.round_number == 1:
            prior = C.PRIOR_HIGH
        else:
            prior = self.in_round(self.round_number - 1).hub_posterior

        # Hub observes all signals this round
        signals = [p.signal for p in self.get_players()]
        k = signals.count(C.STATE_HIGH)
        n = len(signals)

        # Likelihoods
        like_high = (q ** k) * ((1 - q) ** (n - k))
        like_low = ((1 - q) ** k) * (q ** (n - k))

        # Bayes rule
        self.hub_posterior = (prior * like_high) / (
            prior * like_high + (1 - prior) * like_low
        )

    def compute_payoffs(self):
        players = self.get_players()
        self.total_contribution = sum(p.contribution_amount() for p in players)

        for p in players:
            p.payoff = (
                C.ENDOWMENT
                - p.contribution_amount()
                + cu(self.mpcr) * self.total_contribution
            )


class Player(BasePlayer):

    # Decision
    contribute = models.BooleanField(
        choices=[[True, "Contribute"], [False, "Do not contribute"]],
        widget=widgets.RadioSelect,
        label="Contribution decision"
    )

    # Belief (not shared)
    belief = models.IntegerField(
        min=0,
        max=100,
        label="Belief that the state is HIGH (0–100)"
    )

    # Private signal
    signal = models.StringField()

    def contribution_amount(self):
        return C.CONTRIBUTION_AMOUNT if self.contribute else cu(0)

    # -----------------------
    # Network helpers
    # -----------------------
    def is_hub(self):
        return self.group.network_type == 'hub' and self.id_in_group == 1

    def ring_neighbors(self):
        n = C.PLAYERS_PER_GROUP
        pid = self.id_in_group
        left_id = n if pid == 1 else pid - 1
        right_id = 1 if pid == n else pid + 1
        return [
            self.group.get_player_by_id(left_id),
            self.group.get_player_by_id(right_id)
        ]

    def draw_noisy_signal(self, true_state: str, accuracy: float):
        if random.random() < accuracy:
            return true_state
        return C.STATE_LOW if true_state == C.STATE_HIGH else C.STATE_HIGH

    # -----------------------
    # Mechanical information exposure
    # -----------------------
    def signals_observed_this_round(self):
        """
        Returns a list of dicts:
        [{'source': <label>, 'signal': <value>}]

        HUB:
          - Observes all players' signals

        SPOKES:
          - Observe own signal
          - (Posterior is shown via template, not here)

        RING:
          - Observe own + two neighbors
        """
        g = self.group
        r = self.round_number

        observed = []

        # Own signal
        observed.append({
            'source': 'You',
            'signal': self.in_round(r).signal
        })

        # Ring
        if g.network_type == 'ring':
            for nb in self.ring_neighbors():
                nb_r = nb.in_round(r)
                observed.append({
                    'source': f'Neighbor {nb_r.id_in_group}',
                    'signal': nb_r.signal
                })
            return observed

        # Hub-and-spoke
        if self.is_hub():
            for p in g.get_players():
                pr = p.in_round(r)
                if pr.id_in_group != self.id_in_group:
                    observed.append({
                        'source': f'Player {pr.id_in_group}',
                        'signal': pr.signal
                    })
            return observed

        # Spoke: only own signal (hub posterior shown separately)
        return observed
