import random as rd
import matplotlib.pyplot as plt
import pylab
import numpy as np
import tensorflow as tf
import time
import sys

from initializeSINDy import initializeSINDy
from sampleGenerator import generateTrainingSample
from dqs import DQSAgent


if __name__ == "__main__":
    with tf.Session() as sesh:
        function_count = 3
        max_order = 3
        max_elements = 3
        coefficient_magnitude = 2
        henkel_rows = 10
        dt = .001

        state_size = 20
        action_size = 41
        training_epochs = 5
        terminal = False
        logs_path = 'logs'
        epochReward = 0
        iteration = 0

        agent = DQSAgent(state_size, action_size, sesh, logs_path)
        sesh.run(tf.initialize_all_variables())

        for epoch in range(training_epochs):
            start = int(round(time.time() * 1000))
            now = int(round(time.time() * 1000))
            data, oracle = generateTrainingSample(function_count, max_order, max_elements, coefficient_magnitude)
            while (np.isnan(data).any() or np.ptp(data) > 100.0 or np.ptp(data) < 1 or now - start > 10000):
                now = int(round(time.time() * 1000))
                data, oracle = generateTrainingSample(function_count, max_order, max_elements, coefficient_magnitude)

            V, dX, theta, norms = initializeSINDy(data[:, 0], henkel_rows, function_count, max_order, dt)
            # state, resid, rank, s = np.linalg.lstsq(theta, dX)
            print("data, dX", data[14:, :].shape, dX.shape)
            state, resid, rank, s = np.linalg.lstsq(theta, data[14:, :])
            epochReward = 0
            done = False

            for dim in range(len(state[0])):
                while done == False:

                    # take next action
                    action = agent.action(state[:, dim])
                    # print("action", action)

                    # get reward (at new state)
                    next_state, reward, done = agent.step(state[:, dim], action, oracle, theta, dX)
                    # print("next state", next_state)
                    epochReward += reward
                    iteration += 1
                    if done:
                        continue

                    # get target value
                    target = agent.target(next_state, action, reward, done)
                    # print("target", target)
                    agent.remember(state[:, dim], action, reward, next_state, done)

                    # train model
                    agent.train(state[:, dim], target, epoch, iteration)

                    # experience replay
                    # if len(agent.memory) > batch_size:
                    #     agent.replay(batch_size, i)
                    
                    # update state for next round
                    state[:, dim] = next_state

                    if iteration % 2000 == 0:
                        print("current state", next_state)

            # record reward at epoch end
            # reward_summary = tf.Summary(value=[tf.Summary.Value(tag="reward", simple_value=epochReward)])
            print("epoch, reward", epoch, epochReward)
            # agent.writer.add_summary(reward_summary, global_step=epochIteration)

    # print("Accuracy: ", accuracy.eval(feed_dict={ x: mnist.test.images, y_: mnist.test.labels }))
    print("done")
    agent.kill()
