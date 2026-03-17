import random
import math
from statistics import mean

N_PLAYERS = 8
N_ROUNDS = 15

def draw_signal(true_state: int, q: float) -> int:
    # true_state: 1 for HIGH, 0 for LOW
    return true_state if random.random() < q else 1 - true_state

def logit(p, eps=1e-9):
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def logistic(x):
    return 1 / (1 + math.exp(-x))

def update_posterior(prior: float, signals: list[int], q: float) -> float:
    """
    Independent signals conditional on state, accuracy q.
    Returns posterior P(HIGH | signals), assuming prior on HIGH.
    """
    # Work in log-odds for numerical stability
    lo = logit(prior)
    # Each HIGH signal adds log(q/(1-q)); each LOW adds log((1-q)/q)
    incr = math.log(q / (1 - q))
    k = sum(signals)            # count of HIGH signals (1s)
    n = len(signals)
    lo_post = lo + (2*k - n) * incr
    return logistic(lo_post)

def ring_neighbors(pid: int) -> tuple[int,int]:
    left = N_PLAYERS if pid == 1 else pid - 1
    right = 1 if pid == N_PLAYERS else pid + 1
    return left, right

def simulate_one_session(q: float, true_state: int, network: str):
    """
    Returns posterior trajectories for:
      - ring: a representative player (pid=2)
      - hub: hub (pid=1) and spoke (pid=2)
    """
    # pre-draw all signals by round and player
    signals = {r: {pid: draw_signal(true_state, q) for pid in range(1, N_PLAYERS+1)}
               for r in range(1, N_ROUNDS+1)}

    prior = 0.5
    traj = {}

    if network == "ring":
        pid = 2
        p = prior
        traj_list = []
        for r in range(1, N_ROUNDS+1):
            l, rr = ring_neighbors(pid)
            obs = [signals[r][pid], signals[r][l], signals[r][rr]]
            p = update_posterior(p, obs, q)  # “ideal” uses last posterior as new prior
            traj_list.append(p)
        traj["ring_player"] = traj_list

    if network == "hub":
        # hub pid=1 sees all 8 signals each round
        p_hub = prior
        hub_list = []
        for r in range(1, N_ROUNDS+1):
            obs = [signals[r][pid] for pid in range(1, N_PLAYERS+1)]
            p_hub = update_posterior(p_hub, obs, q)
            hub_list.append(p_hub)
        traj["hub"] = hub_list

        # spoke pid=2 sees own + hub’s signal each round
        pid = 2
        p_spoke = prior
        spoke_list = []
        for r in range(1, N_ROUNDS+1):
            obs = [signals[r][pid], signals[r][1]]
            p_spoke = update_posterior(p_spoke, obs, q)
            spoke_list.append(p_spoke)
        traj["spoke"] = spoke_list

    return traj

def run_calibration(q_values, n_runs=2000, threshold=0.8, seed=1):
    random.seed(seed)
    results = []
    for q in q_values:
        # evaluate both states for symmetry
        for network in ["ring", "hub"]:
            pass_rate = {"ring_player": [], "hub": [], "spoke": []}

            for true_state in [0, 1]:
                for _ in range(n_runs):
                    traj = simulate_one_session(q, true_state, network)
                    for k, v in traj.items():
                        # “learned” if posterior in TRUE state exceeds threshold by round 10 and round 15
                        # if true_state=0 (LOW), we look at P(HIGH) being low => use 1-p
                        p10 = v[9]
                        p15 = v[14]
                        if true_state == 1:
                            learned10 = (p10 >= threshold)
                            learned15 = (p15 >= threshold)
                        else:
                            learned10 = ((1 - p10) >= threshold)
                            learned15 = ((1 - p15) >= threshold)
                        pass_rate[k].append((learned10, learned15))

            # summarize
            for role, flags in pass_rate.items():
                if not flags:
                    continue
                frac10 = mean([a for a, b in flags])
                frac15 = mean([b for a, b in flags])
                results.append((q, network, role, frac10, frac15))

    # pretty print
    print(f"Threshold: {threshold} (posterior on TRUE state)")
    print("q | network | role | P(learned by R10) | P(learned by R15)")
    print("-"*72)
    for q, network, role, f10, f15 in results:
        print(f"{q:.2f} | {network:4} | {role:11} | {f10:17.3f} | {f15:17.3f}")

if __name__ == "__main__":
    q_values = [0.55, 0.60, 0.65, 0.70, 0.75]
    run_calibration(q_values, n_runs=1000, threshold=0.8, seed=42)
