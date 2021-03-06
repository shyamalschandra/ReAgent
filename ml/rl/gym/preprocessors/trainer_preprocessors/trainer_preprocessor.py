#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All rights reserved.
"""
Preprocess a batch of transitions sampled from the ReplayBuffer for
Trainer.train, which we expect accepts rlt.PreprocessedTrainingBatch.
"""

from typing import Any, Dict

import torch
from ml.rl import types as rlt
from ml.rl.gym.types import TrainerPreprocessor
from ml.rl.parameters import NormalizationParameters


def discrete_dqn_trainer_preprocessor(
    num_actions: int,
    state_normalization: Dict[int, NormalizationParameters],
    device: str = "cpu",
) -> TrainerPreprocessor:
    def preprocess_batch(train_batch: Any) -> rlt.PreprocessedTrainingBatch:
        obs, action, reward, next_obs, next_action, next_reward, terminal, idxs, possible_actions_mask, log_prob = (
            train_batch
        )
        obs = torch.tensor(obs).squeeze(2)
        action = torch.tensor(action)
        reward = torch.tensor(reward).unsqueeze(1)
        next_obs = torch.tensor(next_obs).squeeze(2)
        next_action = torch.tensor(next_action)
        not_terminal = 1.0 - torch.tensor(terminal).unsqueeze(1).float()
        possible_actions_mask = torch.tensor(possible_actions_mask)
        next_possible_actions_mask = not_terminal.repeat(1, num_actions)
        log_prob = torch.tensor(log_prob)
        assert (
            action.size(1) == num_actions
        ), f"action size(1) is {action.size(1)} while num_actions is {num_actions}"
        return rlt.PreprocessedTrainingBatch(
            training_input=rlt.PreprocessedDiscreteDqnInput(
                state=rlt.PreprocessedFeatureVector(float_features=obs),
                action=action,
                next_state=rlt.PreprocessedFeatureVector(float_features=next_obs),
                next_action=next_action,
                possible_actions_mask=possible_actions_mask,
                possible_next_actions_mask=next_possible_actions_mask,
                reward=reward,
                not_terminal=not_terminal,
                step=None,
                time_diff=None,
            ),
            extras=rlt.ExtraData(
                mdp_id=None,
                sequence_number=None,
                action_probability=log_prob.exp(),
                max_num_actions=None,
                metrics=None,
            ),
        )

    return preprocess_batch


def parametric_dqn_trainer_preprocessor(
    num_actions: int, state_normalization: Dict[int, NormalizationParameters]
) -> TrainerPreprocessor:
    def preprocess_batch(train_batch: Any) -> rlt.PreprocessedTrainingBatch:
        obs, action, reward, next_obs, next_action, next_reward, terminal, idxs, possible_actions_mask, log_prob = (
            train_batch
        )
        batch_size = obs.shape[0]

        obs = torch.tensor(obs).squeeze(2)
        action = torch.tensor(action).float()
        next_obs = torch.tensor(next_obs).squeeze(2)
        next_action = torch.tensor(next_action).to(torch.float32)
        reward = torch.tensor(reward).unsqueeze(1)
        not_terminal = 1 - torch.tensor(terminal).unsqueeze(1).to(torch.uint8)
        possible_actions_mask = torch.ones_like(action).to(torch.bool)

        tiled_next_state = torch.repeat_interleave(
            next_obs, repeats=num_actions, axis=0
        )
        possible_next_actions = torch.eye(num_actions).repeat(batch_size, 1)
        possible_next_actions_mask = not_terminal.repeat(1, num_actions).to(torch.bool)
        return rlt.PreprocessedTrainingBatch(
            rlt.PreprocessedParametricDqnInput(
                state=rlt.PreprocessedFeatureVector(float_features=obs),
                action=rlt.PreprocessedFeatureVector(float_features=action),
                next_state=rlt.PreprocessedFeatureVector(float_features=next_obs),
                next_action=rlt.PreprocessedFeatureVector(float_features=next_action),
                possible_actions=None,
                possible_actions_mask=possible_actions_mask,
                possible_next_actions=rlt.PreprocessedFeatureVector(
                    float_features=possible_next_actions
                ),
                possible_next_actions_mask=possible_next_actions_mask,
                tiled_next_state=rlt.PreprocessedFeatureVector(
                    float_features=tiled_next_state
                ),
                reward=reward,
                not_terminal=not_terminal,
                step=None,
                time_diff=None,
            ),
            extras=rlt.ExtraData(),
        )

    return preprocess_batch


def sac_trainer_preprocessor() -> TrainerPreprocessor:
    def preprocess_batch(train_batch: Any) -> rlt.PreprocessedTrainingBatch:
        obs, action, reward, next_obs, next_action, next_reward, terminal, idxs, possible_actions_mask, log_prob = (
            train_batch
        )
        obs = torch.tensor(obs).squeeze(2)
        action = torch.tensor(action).float()
        reward = torch.tensor(reward).unsqueeze(1)
        next_obs = torch.tensor(next_obs).squeeze(2)
        next_action = torch.tensor(next_action)
        not_terinal = 1.0 - torch.tensor(terminal).unsqueeze(1).float()
        idxs = torch.tensor(idxs)
        possible_actions_mask = torch.tensor(possible_actions_mask).float()
        log_prob = torch.tensor(log_prob)
        return rlt.PreprocessedTrainingBatch(
            training_input=rlt.PreprocessedPolicyNetworkInput(
                state=rlt.PreprocessedFeatureVector(float_features=obs),
                action=rlt.PreprocessedFeatureVector(float_features=action),
                next_state=rlt.PreprocessedFeatureVector(float_features=next_obs),
                next_action=rlt.PreprocessedFeatureVector(float_features=next_action),
                reward=reward,
                not_terminal=not_terinal,
                step=None,
                time_diff=None,
            ),
            extras=rlt.ExtraData(),
        )

    return preprocess_batch
