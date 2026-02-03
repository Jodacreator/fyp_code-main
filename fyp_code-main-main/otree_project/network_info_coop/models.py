from otree.api import *
import random

doc = """
Network Information & Cooperation (signals-only):
- Fixed hidden state (HIGH/LOW) across rounds
- Per-round noisy private signals
- Mechanical signal sharing via static network (hub-spoke vs ring)
- Repeated public goods game (continuous contribution 0–20)
- Non-incentivized belief elicitation (not shared)
"""


class C(BaseConstants):
    NAME_IN_URL = 'network_info_coop'
    PLAYERS_PER_GROUP = 8
    NUM_ROUNDS = 15

    # Public goods
    ENDOWMENT = cu(20)
    MIN_CONTRIBUTION = cu(0)
    MAX_CONTRIBUTION = cu(20)

    # MPCR depends on state (held constant across treatments)
    MPCR_HIGH = 0.70
    MPCR_LOW = 0.30

    # Hidden state + signals
    STATE_HIGH = "HIGH"
    STATE_LOW = "LOW"
    SIGNAL_ACCURACY = 0.60  # P(signal = true_state)


class Subsession(BaseSubsession):
    def creating_session(self):
        for g in self.get_groups():
            # Treatment assignment (session-level config)
            g.network_type = (self.session.config.get('network_type', 'ring') or 'ring').strip().lower()
            if g.network_type not in ('ring', 'hub'):
                g.network_type = 'ring'

            # Fixed hidden state across rounds (per group)
            if self.round_number == 1:
                g.state = random.choice([C.STATE_HIGH, C.STATE_LOW])
            else:
                g.state = g.in_round(1).state

            # Set mpcr given hidden state
            g.mpcr = C.MPCR_HIGH if g.state == C.STATE_HIGH else C.MPCR_LOW

            # Assign hub ONCE per group (only relevant for hub network) and keep fixed across rounds
            if g.network_type == 'hub':
                if self.round_number == 1:
                    g.hub_id = random.randint(1, C.PLAYERS_PER_GROUP)
                else:
                    g.hub_id = g.in_round(1).hub_id
            else:
                # Optional: keep it defined for ring as well
                g.hub_id = 0

            # Draw private signals each round
            for p in g.get_players():
                p.signal = p.draw_noisy_signal(true_state=g.state, accuracy=C.SIGNAL_ACCURACY)


class Group(BaseGroup):
    network_type = models.StringField()
    state = models.StringField()
    mpcr = models.FloatField()

    total_contribution = models.CurrencyField(initial=0)

    # For hub-and-spoke network: randomly chosen once at round 1, then fixed
    hub_id = models.IntegerField()

    def hub_player(self):
        return self.get_player_by_id(self.hub_id)

    def compute_payoffs(self):
        players = self.get_players()
        self.total_contribution = sum(p.contribution for p in players)

        # IMPORTANT: multiply as float first, then convert once to Currency
        total_float = float(self.total_contribution)

        for p in players:
            p.payoff = (
                C.ENDOWMENT
                - p.contribution
                + cu(self.mpcr * total_float)
            )


class Player(BasePlayer):
   # -----------------------
# Comprehension check (Round 1)
# -----------------------
    cq_payoff = models.IntegerField(
        label="How is your payoff calculated each round?",
        choices=[
            [1, "Endowment − my contribution + MPCR × (total group contribution)"],
            [2, "Endowment + my contribution"],
            [3, "MPCR × my own contribution only"],
            [4, "My payoff is random"],
        ],
        widget=widgets.RadioSelect
    )

    cq_mpcr = models.IntegerField(
        label="What determines whether MPCR is HIGH or LOW?",
        choices=[
            [1, "Your belief report"],
            [2, "Majority of players contributing"],
            [3, "A hidden state chosen at the start"],
            [4, "It changes randomly every round"],
        ],
        widget=widgets.RadioSelect
    )

    cq_state = models.IntegerField(
        label="Once chosen, how does the HIGH/LOW state evolve over rounds?",
        choices=[
            [1, "It changes every round"],
            [2, "It stays fixed for all rounds"],
            [3, "The hub can change it"],
            [4, "Players vote to change it"],
        ],
        widget=widgets.RadioSelect
    )

    cq_network = models.IntegerField(
        label="What signals can you observe each round?",
        choices=[
            [1, "Everyone’s signals"],
            [2, "Only your own signal"],
            [3, "Your signal + signals of players you are connected to"],
            [4, "Signals are never shown"],
        ],
        widget=widgets.RadioSelect
    )

    cq_belief = models.IntegerField(
        label="What is the purpose of the belief report (0–100)?",
        choices=[
            [1, "It affects your payoff"],
            [2, "It is shared with other players"],
            [3, "It determines the hidden state"],
            [4, "It is recorded for the study but does not affect payoffs"],
        ],
        widget=widgets.RadioSelect
    )


    # Decision: continuous contribution
    contribution = models.CurrencyField(
        min=C.MIN_CONTRIBUTION,
        max=C.MAX_CONTRIBUTION,
        label="How much do you contribute to the shared financial investment project? (0–20)"
    )

    # Belief (not shared, not incentivized)
    belief = models.IntegerField(
        min=0,
        max=100,
        label="Belief that the state is HIGH (0–100)"
    )

    # Private signal
    signal = models.StringField()

    # -----------------------
    # Network helpers
    # -----------------------
    def is_hub(self):
        return self.group.network_type == 'hub' and self.id_in_group == self.group.hub_id

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

        RING:
          - Observe own + two neighbors

        HUB-AND-SPOKE:
          - Hub observes all players' signals
          - Non-hub nodes observe own + hub signal
        """
        g = self.group
        r = self.round_number

        observed = []

        # Own signal
        observed.append({
            'source': 'You',
            'signal': self.in_round(r).signal
        })

        # Ring: neighbors
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
            # Hub sees everyone
            for p in g.get_players():
                pr = p.in_round(r)
                if pr.id_in_group != self.id_in_group:
                    observed.append({
                        'source': f'Player {pr.id_in_group}',
                        'signal': pr.signal
                    })
            return observed

        # Non-hub: own + hub signal
        hub = g.hub_player().in_round(r)
        observed.append({
            'source': f'Hub (Player {g.hub_id})',
            'signal': hub.signal
        })
        return observed

    def signals_history(self):
        """History of observed signals from Round 1 up to the current round."""
        hist = []
        for r in range(1, self.round_number + 1):
            pr = self.in_round(r)
            hist.append(dict(round=r, observed=pr.signals_observed_this_round()))
        return hist

    def cumulative_payoff(self):
        """
        Cumulative payoff up to (and including) the most recent round
        for which payoffs have been computed.
        """
        total = cu(0)
        for pr in self.in_all_rounds():
            if pr.payoff is not None:
                total += pr.payoff
        return total
