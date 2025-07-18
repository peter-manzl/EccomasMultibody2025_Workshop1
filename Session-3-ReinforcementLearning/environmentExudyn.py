#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is based on an EXUDYN example
#
# Details:   This file contains an exudyn implementation of the gym environment "cartpole" 
#            and is based on the Exudyn example "OpenAIgymNLinkAdvanced". 
#
# Author:    Johannes Gerstmayr, Peter Manzl
# Notes:     requires pip install stable-baselines3[extra]
# 
# Copyright: This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or 
#            modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import exudyn as exu
from exudyn.utilities import ObjectGround, VObjectGround, RigidBodyInertia, HTtranslate, HTtranslateY, \
                            MarkerNodeCoordinate, LoadCoordinate, LoadSolutionFile, HT0
import exudyn.graphics as graphics
# use robotics implementation for minimum coordinates instead of redundant. 
from exudyn.robotics import Robot, RobotLink, VRobotLink, RobotBase, VRobotBase, RobotTool, VRobotTool
from exudyn.artificialIntelligence import OpenAIGymInterfaceEnv, spaces, logger
import numpy as np

import gymnasium as gym

from stable_baselines3.common.callbacks import BaseCallback

# helper for creating vectorized environment
def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Utility function for multiprocessed env.
    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the initial seed for RNG
    :param rank: index of the subprocess
    """
    def _init():
        env = gym.make(env_id) # , render_mode="rgb_array")
        env.reset(seed=seed + rank)
        return env
    set_random_seed(seed)
    return _init

def make_env_custom(**kwargs):
    def _init():
        env = InvertedNPendulumEnv(**kwargs)
        return env
    return _init
    
    
#derive class from logger to log additional information
#this is needed for vectorized environments, where reward is not logged automatically
class RewardLoggingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(RewardLoggingCallback, self).__init__(verbose)

    #log mean values at rollout end
    def _on_rollout_end(self) -> bool:
        if 'infos' in self.locals:
            info = self.locals['infos'][-1]
            # print('infos:', info)
            if 'rewardMean' in info:
                self.logger.record("rollout/rewardMean", info['rewardMean'])
            if 'episodeLen' in info:
                self.logger.record("rollout/episodeLen", info['episodeLen'])
            if 'rewardSum' in info:
                self.logger.record("rollout/rewardSum", info['rewardSum'])

    #log (possibly) every step 
    def _on_step(self) -> bool:
        #extract local variables to find reward
        if 'infos' in self.locals:
            info = self.locals['infos'][-1]

            if 'reward' in info:
                self.logger.record("train/reward", info['reward'])
            #for SAC / A2C in non-vectorized envs, per episode:
            if 'episode' in info and 'r' in info['episode']:
                self.logger.record("episode/reward", info['episode']['r'])
        return True
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



class InvertedNPendulumEnv(OpenAIGymInterfaceEnv):
    #**classFunction: OVERRIDE this function to create multibody system mbs and setup simulationSettings; call Assemble() at the end!
    #                 you may also change SC.visualizationSettings() individually; kwargs may be used for special setup
    def CreateMBS(self, SC, mbs, simulationSettings, **kwargs):
        #%%++++++++++++++++++++++++++++++++++++++++++++++
        #this model uses kwargs: thresholdFactor
        
        # self.steps_beyond_done = False
        thresholdFactor = 1
        
        if 'nLinks' in kwargs: 
            self.nLinks = kwargs['nLinks']
        else: 
            self.nLinks = 1
        if 'flagContinuous' in kwargs: 
            self.flagContinuous = kwargs['flagContinuous']
        else: 
            self.flagContinuous = True 
        self.nTotalLinks = self.nLinks+1 # the (prismatically constrained) base is also a link
        
        
        gravity = 9.81
        self.length = 1.
        width = 0.1*self.length
        masscart = 1.
        massarm = 0.1
        total_mass = massarm + masscart
        armInertia = self.length**2*0.5*massarm #for a rod with equally distributed mass, correctly, it would read self.length**2*massarm/3; using here the values of previous research
        
        # environment variables  and force magnitudes and are taken from the  
        # paper "Reliability evaluation of reinforcement learning methods for 
        # mechanical systems with increasing complexity", Manzl et al. 
        
        self.force_mag = 40 # 10 #10*2 works for 7e7 steps; must be larger for triple pendulum to be more reactive ...
        if self.nLinks == 1: 
            self.force_mag = 12
        if self.nLinks == 3: 
            self.force_mag = self.force_mag*1.5 
            thresholdFactor = 2
        if self.nLinks >= 4: 
            self.force_mag = self.force_mag*2.5
            thresholdFactor = 2.5

        if self.flagContinuous: 
            self.force_mag *= 2 #continuous controller can have larger max value

        if 'thresholdFactor' in kwargs:
            thresholdFactor = kwargs['thresholdFactor']

        self.stepUpdateTime = 0.02  # step size for RL-method
        
        background = graphics.CheckerBoard(point= [0,0.5*self.length,-0.5*width], 
                                              normal= [0,0,1], size=10, size2=6, nTiles=20, nTiles2=12)
        
        oGround=self.mbs.AddObject(ObjectGround(referencePosition= [0,0,0],  #x-pos,y-pos,angle
                                           visualization=VObjectGround(graphicsData= [background])))


        #build kinematic tree with Robot class
        L = self.length
        w = width
        gravity3D = [0.,-gravity,0]
        graphicsBaseList = [graphics.Brick(size=[L*4, 0.8*w, 0.8*w], color=graphics.color.grey)] #rail
        
        newRobot = Robot(gravity=gravity3D,
                      base = RobotBase(visualization=VRobotBase(graphicsData=graphicsBaseList)),
                      tool = RobotTool(HT=HTtranslate([0,0.5*L,0]), visualization=VRobotTool(graphicsData=[
                          graphics.Brick(size=[w, L, w], color=graphics.color.orange)])),
                      referenceConfiguration = []) #referenceConfiguration created with 0s automatically
        
        #cart:
        Jlink = RigidBodyInertia(masscart, np.diag([0.1*masscart,0.1*masscart,0.1*masscart]), [0,0,0])
        link = RobotLink(Jlink.Mass(), Jlink.COM(), Jlink.InertiaCOM(), 
                         jointType='Px', preHT=HT0(), 
                         # PDcontrol=(pControl, dControl),
                         visualization=VRobotLink(linkColor=graphics.color.lawngreen))
        newRobot.AddLink(link)
    
        
        
        for i in range(self.nLinks):
            
            Jlink = RigidBodyInertia(massarm, np.diag([armInertia,0.1*armInertia,armInertia]), [0,0.5*L,0]) #only inertia_ZZ is important
            #Jlink = Jlink.Translated([0,0.5*L,0])
            preHT = HT0()
            if i > 0:
                preHT = HTtranslateY(L)
    
            link = RobotLink(Jlink.Mass(), Jlink.COM(), Jlink.InertiaCOM(), 
                             jointType='Rz', preHT=preHT, 
                             #PDcontrol=(pControl, dControl),
                             visualization=VRobotLink(linkColor=graphics.color.blue))
            newRobot.AddLink(link)
        
        self.Jlink = Jlink
        
        
        sKT = []
        dKT = newRobot.CreateKinematicTree(mbs)
        self.oKT = dKT['objectKinematicTree']
        self.nKT = dKT['nodeGeneric']
        
        # sKT+=[mbs.AddSensor(SensorKinematicTree(objectNumber=oKT, linkNumber=self.nTotalLinks-1, 
        #                                         localPosition=locPos, storeInternal=True,
        #                                         outputVariableType=exu.OutputVariableType.Position))]

        #control force
        mCartCoordX = self.mbs.AddMarker(MarkerNodeCoordinate(nodeNumber=self.nKT, coordinate=0))
        self.lControl = self.mbs.AddLoad(LoadCoordinate(markerNumber=mCartCoordX, load=0.))
        
        #%%++++++++++++++++++++++++
        # exudyn specific simulation settings
        self.mbs.Assemble() #computes initial vector        
        self.simulationSettings.timeIntegration.numberOfSteps = 1 #this is the number of solver steps per RL-step
        self.simulationSettings.timeIntegration.endTime = 0 #will be overwritten in step
        self.simulationSettings.timeIntegration.verboseMode = 0
        self.simulationSettings.solutionSettings.writeSolutionToFile = False #set True only for postprocessing
        #self.simulationSettings.timeIntegration.simulateInRealtime = True
        
        self.simulationSettings.timeIntegration.newton.useModifiedNewton = True
        # visualization settings for simulation
        self.SC.visualizationSettings.general.drawWorldBasis=True
        self.SC.visualizationSettings.general.graphicsUpdateInterval = 0.01
        self.SC.visualizationSettings.openGL.multiSampling=4
        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Angle at which to fail the episode
        # these parameters are used in subfunctions
        # self.theta_threshold_radians = thresholdFactor* 18 * 2 * np.pi / 360
        # self.x_threshold = thresholdFactor*3.6
        # harmonize with gymnasium environment
        self.theta_threshold_radians = 24 * np.pi/180
        self.x_threshold = 4.8


        #must return state size
        stateSize = (self.nTotalLinks)*2 #the number of states (position/velocity that are used by learning algorithm)

        #to track mean reward:
        self.rewardCnt = 0
        self.rewardMean = 0

        return stateSize

    #**classFunction: OVERRIDE this function to set up self.action_space and self.observation_space
    def SetupSpaces(self):

        # total space is 2 times larger than space at which we get done
        high = np.array(
            [
                self.x_threshold,
            ] +
            [
                np.inf
             ] +
            [
                self.theta_threshold_radians,
            ] * self.nLinks +
            [                
                np.inf,
            ] * self.nLinks
            ,
            dtype=np.float32,
        )
        
        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++
        #see https://github.com/openai/gym/blob/64b4b31d8245f6972b3d37270faf69b74908a67d/gym/core.py#L16
        #for Env:
        if self.flagContinuous: 
            #action is -1 ... +1, then scaled with self.force_mag
            self.action_space = spaces.Box(low=np.array([-1 ], dtype=np.float32),
                                           high=np.array([1], dtype=np.float32), dtype=np.float32)
        else: 
            self.action_space = spaces.Discrete(2)
        
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++


    #**classFunction: this function is overwritten to map the action given by learning algorithm to the multibody system (environment)
    def MapAction2MBS(self, action):
        if self.flagContinuous: 
            force = action[0] * self.force_mag
        else:     
            force = -self.force_mag if action == 1 else self.force_mag        
        self.mbs.SetLoadParameter(self.lControl, 'load', force)

    #**classFunction: this function is overwrritten to collect output of simulation and map to self.state tuple
    #**output: return bool done which contains information if system state is outside valid range
    def Output2StateAndDone(self):
        
        #+++++++++++++++++++++++++
        statesVector =  self.mbs.GetNodeOutput(self.nKT, variableType=exu.OutputVariableType.Coordinates)
        statesVector_t =  self.mbs.GetNodeOutput(self.nKT, variableType=exu.OutputVariableType.Coordinates_t)
        # self.state = tuple(list(statesVector) + list(statesVector_t)) #sorting different from previous implementation
        self.state = tuple([statesVector[0]] + [statesVector_t[0]] + list(statesVector[1:]) + list(statesVector_t[1:]))
        cartPosX = statesVector[0]

        done = bool(
            cartPosX < -self.x_threshold
            or cartPosX > self.x_threshold
            or max(statesVector[1:self.nTotalLinks]) > self.theta_threshold_radians 
            or min(statesVector[1:self.nTotalLinks]) < -self.theta_threshold_radians 
            # or self.rewardCnt > 2000 # here the environment could also be reset if it managed to stabilize for N_episode_max steps. 
            )
        # print("cartPosX: ", cartPosX, ", done: ", done) 
        return done

    
    #**classFunction: OVERRIDE this function to maps the current state to mbs initial values
    #**output: return [initialValues, initialValues\_t] where initialValues[\_t] are ODE2 vectors of coordinates[\_t] for the mbs
    def State2InitialValues(self):
        #+++++++++++++++++++++++++++++++++++++++++++++
        initialValues = [self.state[0]] + list(self.state[2:self.nTotalLinks+1])
        initialValues_t = [self.state[1]] + list(self.state[self.nTotalLinks+1:])
               
        #set initial values into mbs immediately
        self.mbs.systemData.SetODE2Coordinates(initialValues, exu.ConfigurationType.Initial)
        self.mbs.systemData.SetODE2Coordinates_t(initialValues_t, exu.ConfigurationType.Initial)

        #this function is only called at reset(); so, we can use it to reset the mean reward:
        self.rewardCnt = 0
        self.rewardMean = 0

        return [initialValues,initialValues_t]
    
    #**classFunction: this is the objective which the RL method tries to maximize (average expected reward)
    def getReward(self): 
        #reward = 1 - 0.5 * abs(self.state[0])/self.x_threshold - 0.5 * abs(self.state[1]) / self.theta_threshold_radians
        
        reward = 1 - 0.5 * abs(self.state[0])/self.x_threshold- 0.5 * abs(self.state[2]) / self.theta_threshold_radians

        if reward < 0: reward = 0

        return reward 

    #**classFunction: openAI gym interface function which is called to compute one step
    def step(self, action):
        err_msg = f"{action!r} ({type(action)}) invalid"
        assert self.action_space.contains(action), err_msg
        assert self.state is not None, "Call reset before using step method."
        
        #++++++++++++++++++++++++++++++++++++++++++++++++++
        #main steps:
        #initial values only set in reset function!
        # [initialValues,initialValues_t] = self.State2InitialValues()
        # self.mbs.systemData.SetODE2Coordinates(initialValues, exu.ConfigurationType.Initial)
        # self.mbs.systemData.SetODE2Coordinates_t(initialValues_t, exu.ConfigurationType.Initial)

        self.MapAction2MBS(action)
        
        #this may be time consuming for larger/more complicated models!
        self.IntegrateStep()
        
        done = self.Output2StateAndDone()
        # print('state:', self.state, 'done: ', done)
        #++++++++++++++++++++++++++++++++++++++++++++++++++
        #compute reward and done

        if not done:
            reward = self.getReward()
        elif self.steps_beyond_done is None:
            # system just fell down
            self.steps_beyond_done = 0
            reward = self.getReward()
        else:
            
            if self.steps_beyond_done == 0:
                logger.warn(
                    "You are calling 'step()' even though this "
                    "environment has already returned done = True. You "
                    "should always call 'reset()' once you receive 'done = "
                    "True' -- any further steps are undefined behavior."
                )
            self.steps_beyond_done += 1
            reward = 0.0

        self.rewardCnt += 1
        self.rewardMean += reward

        info = {'reward': reward} #put reward into info for logger

        #compute mean values per episode:
        if self.rewardCnt != 0: #per epsiode
            info['rewardMean'] = self.rewardMean / self.rewardCnt
            info['rewardSum'] = self.rewardMean
            info['episodeLen'] = self.rewardCnt

        terminated, truncated = done, False # since stable-baselines3 > 1.8.0 implementations terminated and truncated 
        return np.array(self.state, dtype=np.float32), reward, terminated, truncated, info

if __name__ == '__main__': 
    from stable_baselines3 import A2C, SAC
    
    modelType = 'A2C'
    modelName = 'A2C_cartPole_2025-07-05_11-36-22'
    if modelType == 'A2C': 
        model = A2C.load("solution/" + modelName)
    elif modelType == 'SAC': 
        model = SAC.load("solution/" + modelName)
    
    env = InvertedNPendulumEnv(thresholdFactor=5, nLinks=1, flagContinuous=True) #larger threshold for testing
    
    solutionFile='solution/learningCoordinates.txt'
    env.TestModel(numberOfSteps=1000, model=model, solutionFileName=solutionFile, 
                  stopIfDone=False, useRenderer=False, sleepTime=0) #just compute solution file

    #++++++++++++++++++++++++++++++++++++++++++++++
    #visualize (and make animations) in exudyn:
    from exudyn.interactive import SolutionViewer
    from exudyn.utilities import LoadSolutionFile
    
    env.SC.visualizationSettings.general.autoFitScene = False
    solution = LoadSolutionFile(solutionFile)
    
    SolutionViewer(env.mbs, solution, timeout=0.005, rowIncrement=2) #loads solution file via name stored in mbs

