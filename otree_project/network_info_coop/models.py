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

    # Prior is 50/50 by design (informational only; not needed for payoffs)
    PRIOR_HIGH = 0.5


class Subsession(BaseSubsession):
    def creating_session(self):
        for g in self.get_groups():
            # Treatment: static network
            g.network_type = (self.session.config.get('network_type', 'ring') or 'ring').strip().lower()
            if g.network_type not in ('ring', 'hub'):
                g.network_type = 'ring'

            # Fixed state across all rounds
            if self.round_number == 1:
                g.state = random.choice([C.STATE_HIGH, C.STATE_LOW])
            else:
                g.state = g.in_round(1).state

            g.mpcr = C.MPCR_HIGH if g.state == C.STATE_HIGH else C.MPCR_LOW

            # Per-round i.i.d. private signals for all players
            for p in g.get_players():
                p.signal = p.draw_noisy_signal(true_state=g.state, accuracy=C.SIGNAL_ACCURACY)


class Group(BaseGroup):
    network_type = models.StringField()
    state = models.StringField()
    mpcr = models.FloatField()

    total_contribution = models.CurrencyField(initial=0)

    def hub_player(self):
        # Hub fixed as player 1 for now (fine for trial runs; can randomise later)
        return self.get_player_by_id(1)

    def compute_payoffs(self):
        players = self.get_players()
        self.total_contribution = sum(p.contribution_amount() for p in players)

        for p in players:
            p.payoff = C.ENDOWMENT - p.contribution_amount() + cu(self.mpcr) * self.total_contribution


class Player(BasePlayer):
    # Decision: binary contribution
    contribute = models.BooleanField(
        choices=[[True, "Contribute"], [False, "Do not contribute"]],
        widget=widgets.RadioSelect,
        label="Contribution decision"
    )

    # Non-incentivized belief (0–100): never shown to others
    belief = models.IntegerField(min=0, max=100, label="Belief that the state is HIGH (0–100)")

    # Private signal each round
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
        return [self.group.get_player_by_id(left_id), self.group.get_player_by_id(right_id)]

    def draw_noisy_signal(self, true_state: str, accuracy: float):
        if random.random() < accuracy:
            return true_state
        return C.STATE_LOW if true_state == C.STATE_HIGH else C.STATE_HIGH

    # -----------------------
    # Mechanical information exposure (signals only)
    # -----------------------
    def signals_observed_this_round(self):
        """
        Returns a list of dicts: [{'source': <label>, 'signal': 'HIGH'/'LOW'}, ...]

        HUB treatment:
          - Hub observes ALL players' signals (including own)
          - Spokes observe ONLY:
              • their own private signal
              • the hub's signal

        RING treatment:
          - Each player observes:
              • own signal
              • left neighbor signal
              • right neighbor signal
        """
        g = self.group
        r = self.round_number

        observed = []

        # Always observe own signal
        me = self.in_round(r)
        observed.append({'source': 'You', 'signal': me.signal})

        # Ring network: see 2 neighbors
        if g.network_type == 'ring':
            for nb in self.ring_neighbors():
                nb_r = nb.in_round(r)
                observed.append({'source': f'Neighbor {nb_r.id_in_group}', 'signal': nb_r.signal})
            return observed

        # Hub-and-spoke network
        hub = g.hub_player().in_round(r)

        if self.is_hub():
            # Hub sees everyone else
            for p in g.get_players():
                pr = p.in_round(r)
                if pr.id_in_group != self.id_in_group:
                    observed.append({'source': f'Player {pr.id_in_group}', 'signal': pr.signal})
            return observed

        # Spoke: sees hub only (no other spokes)
        observed.append({'source': 'Hub', 'signal': hub.signal})
        return observed
