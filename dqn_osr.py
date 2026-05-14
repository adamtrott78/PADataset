import copy
import json
import os
import time
import random
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from osr_core import BaseOSRMethod, BackbonePayload, SplitOutputs



def _write_dqn_progress(**payload) -> None:
    path = os.environ.get("PADATASET_OSR_PROGRESS_JSON")
    if not path:
        return
    try:
        p = Path(path)
        current = {}
        if p.is_file():
            try:
                current = json.loads(p.read_text())
            except Exception:
                current = {}
        current.update(payload)
        current.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(current, indent=2))
        tmp.replace(p)
    except Exception:
        pass


# ============================================================
# confidence-state helpers
# ============================================================

def compute_entropy_from_probs(probs: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    probs = np.clip(probs, eps, 1.0 - eps)
    return -np.sum(probs * np.log(probs), axis=1)


def compute_top2_gap_from_probs(probs: np.ndarray) -> np.ndarray:
    sorted_probs = np.sort(probs, axis=1)
    return sorted_probs[:, -1] - sorted_probs[:, -2]


def compute_energy_from_logits(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    scaled = logits / float(temperature)
    return (
        float(temperature)
        * torch.logsumexp(torch.tensor(scaled, dtype=torch.float32), dim=1)
    ).numpy()


def compute_logit_variance(logits: np.ndarray) -> np.ndarray:
    abs_logits = np.abs(logits)
    return np.var(abs_logits - abs_logits.mean(axis=1, keepdims=True), axis=1)


def compute_dqn_state_from_split(
    split: SplitOutputs,
    state_mode: str = "softmax3",
    energy_temperature: float = 1.0,
) -> np.ndarray:
    """
    state_mode:
      - 'softmax3'  -> [P1, P1-P2, entropy]
      - 'expanded5' -> [P1, P1-P2, entropy, energy, variance]
    """
    probs = split.probs
    logits = split.logits

    p1 = np.max(probs, axis=1)
    p1_p2 = compute_top2_gap_from_probs(probs)
    ent = compute_entropy_from_probs(probs)

    if state_mode == "softmax3":
        state = np.stack([p1, p1_p2, ent], axis=1)

    elif state_mode == "expanded5":
        energy = compute_energy_from_logits(logits, temperature=energy_temperature)
        var = compute_logit_variance(logits)
        state = np.stack([p1, p1_p2, ent, energy, var], axis=1)

    else:
        raise ValueError(f"Unsupported state_mode: {state_mode}")

    return state.astype(np.float32)


def cosine_similarity_vec(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < eps or nb < eps:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def running_centroid_update(
    centroid: np.ndarray,
    count: int,
    state: np.ndarray,
) -> Tuple[np.ndarray, int]:
    new_count = count + 1
    new_centroid = (centroid * count + state) / new_count
    return new_centroid.astype(np.float32), new_count


# ============================================================
# DQN network
# ============================================================

class QNet(nn.Module):
    def __init__(self, state_size: int, action_size: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DQNAgent:
    """
    Faithful PyTorch port of the TensorFlow notebook agent.
    Actions:
      0 = unknown
      1 = known
    """
    def __init__(
        self,
        state_size: int,
        action_size: int = 2,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.99,
        learning_rate: float = 1e-3,
        memory_size: int = 2000,
        device: str = "cpu",
    ):
        self.state_size = int(state_size)
        self.action_size = int(action_size)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self.epsilon_min = float(epsilon_min)
        self.epsilon_decay = float(epsilon_decay)
        self.learning_rate = float(learning_rate)
        self.device = device

        self.memory = deque(maxlen=int(memory_size))

        self.model = QNet(state_size=self.state_size, action_size=self.action_size).to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.loss_fn = nn.MSELoss()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def predict_q(self, states: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(states, dtype=torch.float32, device=self.device)
            q = self.model(x).cpu().numpy()
        return q

    def act(self, state: np.ndarray) -> int:
        if np.random.rand() <= self.epsilon:
            return random.randint(0, self.action_size - 1)
        q = self.predict_q(state[None, :])[0]
        return int(np.argmax(q))

    def replay(self, batch_size: int = 32):
        if len(self.memory) < batch_size:
            return None

        minibatch = random.sample(self.memory, batch_size)

        states = np.stack([m[0] for m in minibatch], axis=0).astype(np.float32)
        actions = np.array([m[1] for m in minibatch], dtype=np.int64)
        rewards = np.array([m[2] for m in minibatch], dtype=np.float32)
        next_states = np.stack([m[3] for m in minibatch], axis=0).astype(np.float32)
        dones = np.array([m[4] for m in minibatch], dtype=np.float32)

        states_t = torch.tensor(states, dtype=torch.float32, device=self.device)
        next_states_t = torch.tensor(next_states, dtype=torch.float32, device=self.device)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device)

        self.model.train()

        q_values = self.model(states_t)
        q_selected = q_values[torch.arange(batch_size, device=self.device), actions]

        with torch.no_grad():
            next_q_values = self.model(next_states_t)
            next_q_max = next_q_values.max(dim=1).values
            targets = rewards_t + (1.0 - dones_t) * self.gamma * next_q_max

        loss = self.loss_fn(q_selected, targets)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())

    def decay_epsilon(self) -> None:
        # Notebook-faithful behavior: decay once per episode, not once per replay minibatch.
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


# ============================================================
# OSR head
# ============================================================

class DQNOSR(BaseOSRMethod):
    method_name = "dqn_osr"

    def __init__(
        self,
        state_mode: str = "softmax3",
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.99,
        learning_rate: float = 1e-3,
        memory_size: int = 2000,
        batch_size: int = 32,
        episodes: int = 30,
        anchor_fraction: float = 0.05,
        train_subsample_size: int = 1250,
        centroid_update_threshold: float = 0.75,
        energy_temperature: float = 1.0,
        seed: int = 42,
        device: str = "cpu",
    ):
        self.state_mode = str(state_mode)
        if self.state_mode == "softmax3":
            self.state_size = 3
        elif self.state_mode == "expanded5":
            self.state_size = 5
        else:
            raise ValueError(f"Unsupported state_mode: {self.state_mode}")

        self.action_size = 2

        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self.epsilon_min = float(epsilon_min)
        self.epsilon_decay = float(epsilon_decay)
        self.learning_rate = float(learning_rate)
        self.memory_size = int(memory_size)

        self.batch_size = int(batch_size)
        self.episodes = int(episodes)
        self.anchor_fraction = float(anchor_fraction)
        self.train_subsample_size = int(train_subsample_size)
        self.centroid_update_threshold = float(centroid_update_threshold)
        self.energy_temperature = float(energy_temperature)
        self.seed = int(seed)
        self.device = device

        self.agent: Optional[DQNAgent] = None
        self.centroid_known_: Optional[np.ndarray] = None
        self.centroid_unknown_: Optional[np.ndarray] = None
        self.centroid_known_count_: int = 0
        self.centroid_unknown_count_: int = 0

        self.train_history_: list[dict] = []
        self.fitted_ = False
        self.last_fit_summary_: Dict[str, Any] = {}

    # --------------------------------------------------------
    # internal helpers
    # --------------------------------------------------------
    def _set_seed(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)

    def _combine_calibration_states(
        self,
        known_split: SplitOutputs,
        open_split: SplitOutputs,
    ) -> np.ndarray:
        known_states = compute_dqn_state_from_split(
            known_split,
            state_mode=self.state_mode,
            energy_temperature=self.energy_temperature,
        )
        open_states = compute_dqn_state_from_split(
            open_split,
            state_mode=self.state_mode,
            energy_temperature=self.energy_temperature,
        )
        states = np.concatenate([known_states, open_states], axis=0).astype(np.float32)
        return states

    def _build_anchor_masks(self, states: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Faithful to notebook:
          anchors selected from top/bottom 5% by P1 only
        """
        p1 = states[:, 0]
        n = len(states)
        k = max(1, int(self.anchor_fraction * n))

        sorted_idx = np.argsort(p1)
        low_idx = sorted_idx[:k]
        high_idx = sorted_idx[-k:]

        high_mask = np.zeros(n, dtype=bool)
        low_mask = np.zeros(n, dtype=bool)
        high_mask[high_idx] = True
        low_mask[low_idx] = True
        return high_mask, low_mask

    def _init_centroids(
        self,
        states: np.ndarray,
        high_mask: np.ndarray,
        low_mask: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, int, int]:
        c_known = states[high_mask].mean(axis=0).astype(np.float32)
        c_unknown = states[low_mask].mean(axis=0).astype(np.float32)
        n_known = int(high_mask.sum())
        n_unknown = int(low_mask.sum())
        return c_known, c_unknown, n_known, n_unknown

    def _reward_and_target_action(
        self,
        state: np.ndarray,
        c_known: np.ndarray,
        c_unknown: np.ndarray,
    ) -> Tuple[int, float, float, float]:
        sim_known = cosine_similarity_vec(state, c_known)
        sim_unknown = cosine_similarity_vec(state, c_unknown)

        # faithful action semantics:
        # 1 = known, 0 = unknown
        target_action = 1 if sim_known >= sim_unknown else 0
        sim_max = max(sim_known, sim_unknown)

        return target_action, sim_max, sim_known, sim_unknown

    def _fit_from_states(self, states: np.ndarray) -> None:
        self._set_seed()

        high_mask, low_mask = self._build_anchor_masks(states)
        c_known, c_unknown, n_known, n_unknown = self._init_centroids(states, high_mask, low_mask)

        remaining_mask = ~(high_mask | low_mask)
        remaining_states = states[remaining_mask]

        if len(remaining_states) == 0:
            raise RuntimeError("No remaining states after removing anchors for DQN training")

        if len(remaining_states) > self.train_subsample_size:
            rng = np.random.default_rng(self.seed)
            idx = rng.choice(len(remaining_states), size=self.train_subsample_size, replace=False)
            train_states = remaining_states[idx]
        else:
            train_states = remaining_states

        agent = DQNAgent(
            state_size=self.state_size,
            action_size=self.action_size,
            gamma=self.gamma,
            epsilon=self.epsilon,
            epsilon_min=self.epsilon_min,
            epsilon_decay=self.epsilon_decay,
            learning_rate=self.learning_rate,
            memory_size=self.memory_size,
            device=self.device,
        )

        history = []

        _write_dqn_progress(
            phase="dqn_training_start",
            pct=20.0,
            dqn_episode=0,
            dqn_episodes=int(self.episodes),
            dqn_n_states_total=int(len(states)),
            dqn_n_train_states=int(len(train_states)),
            dqn_n_anchor_high=int(high_mask.sum()),
            dqn_n_anchor_low=int(low_mask.sum()),
        )

        for episode in range(self.episodes):
            order = np.random.permutation(len(train_states))
            episode_rewards = []
            losses = []

            for i, idx in enumerate(order):
                state = train_states[idx]

                if i < len(order) - 1:
                    next_state = train_states[order[i + 1]]
                    done = False
                else:
                    next_state = state
                    done = True

                action = agent.act(state)

                target_action, sim_max, sim_known, sim_unknown = self._reward_and_target_action(
                    state,
                    c_known,
                    c_unknown,
                )

                reward = sim_max if action == target_action else -sim_max

                agent.remember(state, action, reward, next_state, done)
                loss = agent.replay(self.batch_size)

                if target_action == 1 and sim_known > self.centroid_update_threshold:
                    c_known, n_known = running_centroid_update(c_known, n_known, state)
                elif target_action == 0 and sim_unknown > self.centroid_update_threshold:
                    c_unknown, n_unknown = running_centroid_update(c_unknown, n_unknown, state)

                episode_rewards.append(float(reward))
                if loss is not None:
                    losses.append(float(loss))

            agent.decay_epsilon()

            avg_reward = float(np.mean(episode_rewards)) if episode_rewards else None
            avg_loss = float(np.mean(losses)) if losses else None
            dqn_pct = 20.0 + 65.0 * float(episode + 1) / float(max(self.episodes, 1))
            _write_dqn_progress(
                phase="dqn_training",
                pct=dqn_pct,
                dqn_episode=int(episode + 1),
                dqn_episodes=int(self.episodes),
                dqn_avg_reward=avg_reward,
                dqn_avg_loss=avg_loss,
                dqn_epsilon=float(agent.epsilon),
                dqn_centroid_known_count=int(n_known),
                dqn_centroid_unknown_count=int(n_unknown),
            )

            history.append({
                "episode": episode + 1,
                "avg_reward": avg_reward,
                "avg_loss": avg_loss,
                "epsilon": float(agent.epsilon),
                "centroid_known": c_known.copy(),
                "centroid_unknown": c_unknown.copy(),
                "n_train_states": int(len(train_states)),
                "n_anchor_high": int(high_mask.sum()),
                "n_anchor_low": int(low_mask.sum()),
            })

        _write_dqn_progress(
            phase="dqn_fit_done",
            pct=85.0,
            dqn_episode=int(self.episodes),
            dqn_episodes=int(self.episodes),
            dqn_final_epsilon=float(agent.epsilon),
            dqn_centroid_known_count=int(n_known),
            dqn_centroid_unknown_count=int(n_unknown),
        )

        self.agent = agent
        self.centroid_known_ = c_known
        self.centroid_unknown_ = c_unknown
        self.centroid_known_count_ = n_known
        self.centroid_unknown_count_ = n_unknown
        self.train_history_ = history
        self.fitted_ = True

        self.last_fit_summary_ = {
            "n_states_total": int(len(states)),
            "n_anchor_high": int(high_mask.sum()),
            "n_anchor_low": int(low_mask.sum()),
            "n_train_states": int(len(train_states)),
            "episodes": self.episodes,
            "final_epsilon": float(agent.epsilon),
            "state_mode": self.state_mode,
            "state_size": self.state_size,
            "centroid_known": c_known.tolist(),
            "centroid_unknown": c_unknown.tolist(),
        }

    # --------------------------------------------------------
    # BaseOSRMethod API
    # --------------------------------------------------------
    def fit(self, payload: BackbonePayload, calibration: Dict[str, Any] | None = None) -> None:
        calibration = calibration or {}

        # Paper-style DQN-IDS fitting uses a mixed confidence-state stream.
        # Do not silently fall back to payload.test_open; that would risk fitting on test data.
        calibration_stream = calibration.get("calibration_stream", None)
        if calibration_stream is not None:
            states = compute_dqn_state_from_split(
                calibration_stream,
                state_mode=self.state_mode,
                energy_temperature=self.energy_temperature,
            )
            self._fit_from_states(states)
            return

        known_split = calibration.get("calibration_known", None)
        open_split = calibration.get("calibration_open", None)

        if known_split is None:
            raise ValueError("DQNOSR.fit() requires explicit calibration_known")
        if open_split is None:
            raise ValueError("DQNOSR.fit() requires explicit calibration_open")

        states = self._combine_calibration_states(known_split, open_split)
        self._fit_from_states(states)
        self.last_fit_summary_.update({
            "n_known_calibration": int(len(known_split.y_true)),
            "n_open_calibration": int(len(open_split.y_true)),
        })

    def score(self, split: SplitOutputs) -> np.ndarray:
        if not self.fitted_ or self.agent is None:
            raise RuntimeError("DQNOSR must be fitted before score()")

        states = compute_dqn_state_from_split(
            split,
            state_mode=self.state_mode,
            energy_temperature=self.energy_temperature,
        )
        q = self.agent.predict_q(states)

        unknown_score = q[:, 0] - q[:, 1]
        return unknown_score.astype(np.float32)

    def predict(self, split: SplitOutputs, unknown_label: int) -> Dict[str, np.ndarray]:
        if not self.fitted_ or self.agent is None:
            raise RuntimeError("DQNOSR must be fitted before predict()")

        states = compute_dqn_state_from_split(
            split,
            state_mode=self.state_mode,
            energy_temperature=self.energy_temperature,
        )
        q = self.agent.predict_q(states)

        # 0 = unknown, 1 = known
        predicted_actions = np.argmax(q, axis=1).astype(int)
        is_unknown = (predicted_actions == 0)

        closed_pred = split.closed_pred.astype(int).copy()
        final_pred = closed_pred.copy()
        final_pred[is_unknown] = int(unknown_label)

        unknown_score = (q[:, 0] - q[:, 1]).astype(np.float32)

        return {
            "unknown_score": unknown_score,
            "is_unknown": is_unknown.astype(bool),
            "closed_pred": closed_pred,
            "final_pred": final_pred,
            "state": states,
            "q_values": q,
            "predicted_actions": predicted_actions,
        }

    def get_params(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "state_mode": self.state_mode,
            "state_size": self.state_size,
            "action_size": self.action_size,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "learning_rate": self.learning_rate,
            "memory_size": self.memory_size,
            "batch_size": self.batch_size,
            "episodes": self.episodes,
            "anchor_fraction": self.anchor_fraction,
            "train_subsample_size": self.train_subsample_size,
            "centroid_update_threshold": self.centroid_update_threshold,
            "energy_temperature": self.energy_temperature,
            "seed": self.seed,
            "device": self.device,
            "fitted": self.fitted_,
            "centroid_known": None if self.centroid_known_ is None else self.centroid_known_.tolist(),
            "centroid_unknown": None if self.centroid_unknown_ is None else self.centroid_unknown_.tolist(),
            "centroid_known_count": self.centroid_known_count_,
            "centroid_unknown_count": self.centroid_unknown_count_,
            "last_fit_summary": copy.deepcopy(self.last_fit_summary_),
            "train_history": copy.deepcopy(self.train_history_),
        }


# ============================================================
# DQN + predicted-class band guard
# ============================================================

def _dqn_guard_safe_percentile(values: np.ndarray, percentiles: Tuple[float, float]) -> Tuple[float, float]:
    lo, hi = percentiles
    return float(np.percentile(values, lo)), float(np.percentile(values, hi))


def _dqn_guard_band_distance(values: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    lo = bounds[:, 0]
    hi = bounds[:, 1]
    below = np.clip(lo - values, 0.0, None)
    above = np.clip(values - hi, 0.0, None)
    raw = below + above
    width = np.maximum(hi - lo, 1e-8)
    return raw / width


class BandedGuardDQNOSR(BaseOSRMethod):
    """
    DQN with predicted-class conditional band veto.

    DQN remains the policy:
      0 = unknown
      1 = known

    But DQN-known decisions must pass known-only predicted-class
    top2/variance/energy bands.
    """

    method_name = "dqn_banded_guard_osr"

    def __init__(
        self,
        state_mode: str = "softmax3",
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.99,
        learning_rate: float = 1e-3,
        memory_size: int = 2000,
        batch_size: int = 32,
        episodes: int = 30,
        anchor_fraction: float = 0.05,
        train_subsample_size: int = 1250,
        centroid_update_threshold: float = 0.75,
        energy_temperature: float = 1.0,
        seed: int = 42,
        device: str = "cpu",
        band_percentiles: Tuple[float, float] = (5.0, 95.0),
        top2_band_percentiles: Tuple[float, float] = (5.0, 95.0),
        band_accept_mode: str = "two_of_three",
        band_weight: float = 1.0,
        min_samples_per_class: int = 5,
        fit_bands_on: str = "predicted_class",
    ):
        self.dqn = DQNOSR(
            state_mode=state_mode,
            gamma=gamma,
            epsilon=epsilon,
            epsilon_min=epsilon_min,
            epsilon_decay=epsilon_decay,
            learning_rate=learning_rate,
            memory_size=memory_size,
            batch_size=batch_size,
            episodes=episodes,
            anchor_fraction=anchor_fraction,
            train_subsample_size=train_subsample_size,
            centroid_update_threshold=centroid_update_threshold,
            energy_temperature=energy_temperature,
            seed=seed,
            device=device,
        )

        self.state_mode = state_mode
        self.energy_temperature = float(energy_temperature)
        self.band_percentiles = tuple(band_percentiles)
        self.top2_band_percentiles = tuple(top2_band_percentiles)
        self.band_accept_mode = str(band_accept_mode)
        self.band_weight = float(band_weight)
        self.min_samples_per_class = int(min_samples_per_class)
        self.fit_bands_on = str(fit_bands_on)

        self.num_classes_: Optional[int] = None
        self.class_names_: Optional[list[str]] = None
        self.band_thresholds_: Optional[Dict[str, Dict[int, Tuple[float, float]]]] = None
        self.fitted_ = False
        self.band_fit_summary_: Dict[str, Any] = {}

    def _compute_band_scores(self, split: SplitOutputs) -> Dict[str, np.ndarray]:
        return {
            "top2": compute_top2_gap_from_probs(split.probs),
            "var": compute_logit_variance(split.logits),
            "energy": compute_energy_from_logits(split.logits, temperature=self.energy_temperature),
        }

    def _labels_for_band_fit(self, split: SplitOutputs) -> np.ndarray:
        if self.fit_bands_on == "predicted_class":
            return split.closed_pred.astype(int)
        if self.fit_bands_on == "true_class":
            return split.y_true.astype(int)
        raise ValueError(f"Unsupported fit_bands_on={self.fit_bands_on!r}")

    def _fit_one_metric_band(
        self,
        values: np.ndarray,
        labels_for_bands: np.ndarray,
        fallback_labels: np.ndarray,
        percentiles: Tuple[float, float],
    ) -> Dict[int, Tuple[float, float]]:
        assert self.num_classes_ is not None
        out: Dict[int, Tuple[float, float]] = {}

        for cls in range(self.num_classes_):
            vals = values[labels_for_bands == cls]
            if vals.size < self.min_samples_per_class:
                vals = values[fallback_labels == cls]
            if vals.size < self.min_samples_per_class:
                vals = values

            out[int(cls)] = _dqn_guard_safe_percentile(vals, percentiles)

        return out

    def _fit_band_guard(self, known_split: SplitOutputs) -> None:
        assert self.num_classes_ is not None

        scores = self._compute_band_scores(known_split)
        labels_for_bands = self._labels_for_band_fit(known_split)
        fallback_labels = known_split.y_true.astype(int)

        self.band_thresholds_ = {
            "top2": self._fit_one_metric_band(
                values=scores["top2"],
                labels_for_bands=labels_for_bands,
                fallback_labels=fallback_labels,
                percentiles=self.top2_band_percentiles,
            ),
            "var": self._fit_one_metric_band(
                values=scores["var"],
                labels_for_bands=labels_for_bands,
                fallback_labels=fallback_labels,
                percentiles=self.band_percentiles,
            ),
            "energy": self._fit_one_metric_band(
                values=scores["energy"],
                labels_for_bands=labels_for_bands,
                fallback_labels=fallback_labels,
                percentiles=self.band_percentiles,
            ),
        }

        self.band_fit_summary_ = {
            "fit_bands_on": self.fit_bands_on,
            "band_percentiles": list(self.band_percentiles),
            "top2_band_percentiles": list(self.top2_band_percentiles),
            "band_accept_mode": self.band_accept_mode,
            "min_samples_per_class": self.min_samples_per_class,
            "thresholds": copy.deepcopy(self.band_thresholds_),
        }

    def _band_predict(self, split: SplitOutputs) -> Dict[str, np.ndarray]:
        if self.band_thresholds_ is None:
            raise RuntimeError("BandedGuardDQNOSR band guard is not fitted")

        scores = self._compute_band_scores(split)
        pred = split.closed_pred.astype(int)

        inside_flags = {}
        distances = {}

        for metric_name in ["top2", "var", "energy"]:
            metric_thresholds = self.band_thresholds_[metric_name]
            bounds = np.array([metric_thresholds[int(c)] for c in pred], dtype=float)
            vals = scores[metric_name]

            inside = (vals >= bounds[:, 0]) & (vals <= bounds[:, 1])
            dist = _dqn_guard_band_distance(vals, bounds)

            inside_flags[metric_name] = inside
            distances[metric_name] = dist

        inside_stack = np.stack(
            [inside_flags["top2"], inside_flags["var"], inside_flags["energy"]],
            axis=1,
        )
        pass_count = inside_stack.sum(axis=1)

        if self.band_accept_mode == "all":
            band_known = pass_count == 3
        elif self.band_accept_mode == "two_of_three":
            band_known = pass_count >= 2
        elif self.band_accept_mode == "any":
            band_known = pass_count >= 1
        elif self.band_accept_mode == "var_energy":
            band_known = inside_flags["var"] & inside_flags["energy"]
        else:
            raise ValueError(f"Unsupported band_accept_mode={self.band_accept_mode!r}")

        dist_stack = np.stack(
            [distances["top2"], distances["var"], distances["energy"]],
            axis=1,
        )
        band_unknown_score = dist_stack.mean(axis=1).astype(np.float32)

        return {
            "band_known": band_known.astype(bool),
            "band_unknown_score": band_unknown_score,
            "band_top2_inside": inside_flags["top2"].astype(bool),
            "band_var_inside": inside_flags["var"].astype(bool),
            "band_energy_inside": inside_flags["energy"].astype(bool),
            "band_top2_distance": distances["top2"].astype(np.float32),
            "band_var_distance": distances["var"].astype(np.float32),
            "band_energy_distance": distances["energy"].astype(np.float32),
            "band_pass_count": pass_count.astype(np.int64),
        }

    def fit(self, payload: BackbonePayload, calibration: Dict[str, Any] | None = None) -> None:
        calibration = calibration or {}

        self.num_classes_ = int(payload.meta["num_classes"])
        self.class_names_ = list(payload.meta["class_names"])

        known_split = calibration.get("calibration_known", None)
        if known_split is None:
            known_split = payload.val_known
        if known_split is None:
            raise ValueError("BandedGuardDQNOSR requires calibration_known or payload.val_known")

        # Fit faithful DQN with the supplied known+open calibration.
        self.dqn.fit(payload, calibration=calibration)

        # Fit guard bands using known calibration only.
        self._fit_band_guard(known_split)

        self.fitted_ = True

    def score(self, split: SplitOutputs) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("BandedGuardDQNOSR must be fitted before score()")

        dqn_score = self.dqn.score(split)
        band = self._band_predict(split)
        return (dqn_score + self.band_weight * band["band_unknown_score"]).astype(np.float32)

    def predict(self, split: SplitOutputs, unknown_label: int) -> Dict[str, np.ndarray]:
        if not self.fitted_:
            raise RuntimeError("BandedGuardDQNOSR must be fitted before predict()")

        dqn_pred = self.dqn.predict(split, unknown_label=unknown_label)
        band = self._band_predict(split)

        dqn_unknown = dqn_pred["is_unknown"].astype(bool)
        dqn_known = ~dqn_unknown

        # DQN-known decisions must pass the predicted-class band guard.
        final_known = dqn_known & band["band_known"]
        is_unknown = ~final_known

        closed_pred = split.closed_pred.astype(int).copy()
        final_pred = closed_pred.copy()
        final_pred[is_unknown] = int(unknown_label)

        unknown_score = (
            dqn_pred["unknown_score"].astype(np.float32)
            + self.band_weight * band["band_unknown_score"].astype(np.float32)
        )

        out = dict(dqn_pred)
        out.update(band)
        out.update({
            "unknown_score": unknown_score.astype(np.float32),
            "is_unknown": is_unknown.astype(bool),
            "closed_pred": closed_pred,
            "final_pred": final_pred,
            "dqn_is_unknown": dqn_unknown.astype(bool),
            "dqn_predicted_actions": dqn_pred["predicted_actions"],
        })
        return out

    def get_params(self) -> Dict[str, Any]:
        dqn_params = self.dqn.get_params()
        return {
            "method_name": self.method_name,
            "state_mode": self.state_mode,
            "band_percentiles": list(self.band_percentiles),
            "top2_band_percentiles": list(self.top2_band_percentiles),
            "band_accept_mode": self.band_accept_mode,
            "band_weight": self.band_weight,
            "min_samples_per_class": self.min_samples_per_class,
            "fit_bands_on": self.fit_bands_on,
            "fitted": self.fitted_,
            "band_fit_summary": copy.deepcopy(self.band_fit_summary_),
            "dqn_params": dqn_params,

            # Flatten common DQN fields for existing reducers.
            "episodes": dqn_params.get("episodes"),
            "anchor_fraction": dqn_params.get("anchor_fraction"),
            "train_subsample_size": dqn_params.get("train_subsample_size"),
            "centroid_update_threshold": dqn_params.get("centroid_update_threshold"),
            "last_fit_summary": dqn_params.get("last_fit_summary"),
            "train_history": dqn_params.get("train_history"),
        }
