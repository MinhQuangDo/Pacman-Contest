from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util
from game import Directions, Actions
import game
from util import nearestPoint

#################
# MDSX #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)


    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}
  
  def getBorder(self, gameState):
    mid = gameState.data.layout.width / 2

    if self.red:
      mid -= 1
    else:
      mid += 1

    legalPositions = [p for p in gameState.getWalls().asList(False) if p[1] > 1]
    border = [p for p in legalPositions if p[0] == mid]
    return border

  
  def aStar(self, gameState, start, goal):
    legalPositions = [p for p in gameState.getWalls().asList(False) if p[1] > 1]

    startCoor = start
    visited = set()
    fringes = util.PriorityQueue()
    fringes.push((startCoor, []), 0)
    actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]

    while not fringes.isEmpty():
        currentCoor, currentPath = fringes.pop()
        if currentCoor == goal:
            return currentPath

        visited.add(currentCoor)
        for action in actions:
          x, y = currentCoor
          dx, dy = Actions.directionToVector(action)
          nextx, nexty = int(x + dx), int(y + dy)
          coorNeighbor = (nextx, nexty)
          if coorNeighbor not in visited and coorNeighbor in legalPositions:
            fringes.push((coorNeighbor, currentPath + [action]), self.getMazeDistance(coorNeighbor, goal))
    return []
    
    
    
    
class OffensiveReflexAgent(ReflexCaptureAgent):
    
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
    
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    foodList = self.getFood(successor).asList()
    features['successorScore'] = self.getScore(successor)
    
    # features['successorScore'] = -len(foodList)
    
    # Compute distance to the nearest food
   
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      minDistanceToFood = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistanceToFood
    
    if action == Directions.STOP: 
      features['stop'] = 1
    else:
      features['stop'] = 0
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: 
      features['reverse'] = 1
    else:
      features['reverse'] = 0
    
    
    features['closeProtector'] = 0  
    # Compute distance to nearest protector 
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    protectors = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer <= 3]
    if len(protectors) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in protectors]
      features['distanceToProtector'] = min(dists)
      nearestProtector = [a for a, v in zip(protectors, dists) if v == min(dists)]
      for d in dists:
        if d <= 1:
          features['closeProtector'] = 1
          break        
    
    # Compute distance to the nearest capsule
    capsuleList = self.getCapsules(successor)
    if len(capsuleList) > 0:
      # features['capsulePresent'] = 1
      minDistanceToCapsule = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
      if features['closeProtector'] == 0:
        features['distanceToCapsule'] = minDistanceToCapsule
      else:
        features['distanceToCapsule'] = minDistanceToCapsule * 5

    

    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -2, 'distanceToProtector': 1, \
      'distanceToCapsule': -2, 'closeProtector': -200,'stop': -300, 'reverse': -2}

class DefensiveReflexAgent(ReflexCaptureAgent):
  def __init__(self, index):
      CaptureAgent.__init__(self, index)
      self.defendingFood = []
      self.target = None
      self.goToFood = False

  
  def chooseAction(self, gameState):

    actions = gameState.getLegalActions(self.index)
    actions.remove(Directions.STOP)
    myPos = gameState.getAgentState(self.index).getPosition()

    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]

    if self.goToFood and len(invaders) == 0:
        actionList = self.aStar(gameState, myPos, self.target)
        if len(actionList) > 0:
          return actionList[0]
        
    values = [self.evaluate(gameState, a) for a in actions]

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]             

    return random.choice(bestActions)

    
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    myFood = self.getFoodYouAreDefending(gameState).asList()
    borderPos = random.choice(self.getBorder(gameState))
    
    if len(self.defendingFood) == 0:
      self.defendingFood = myFood
      self.target = borderPos

    if len(self.defendingFood) > len(myFood):
      target = [food for food in self.defendingFood if food not in myFood][0]
      self.defendingFood = myFood
      self.target = target
      self.goToFood = True
    
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    enemyProtectors = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    
    if len(invaders) > 0:
      invaderDist = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['enemyDistance'] = min(invaderDist)
      
      if features['enemyDistance'] and gameState.getAgentState(self.index).scaredTimer > 0:
        features['onDefense'] = 0
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev:
          features['reverse'] = 1
      self.goToFood = False
      self.target = borderPos
      
    if len(invaders) == 0:
      if len(enemyProtectors) > 0 and not self.goToFood:
        enemyDist = [self.getMazeDistance(myPos, a.getPosition()) for a in enemyProtectors]
        features['enemyDistance'] = min(enemyDist)

      else:
        if len(enemyProtectors) > 0 and self.goToFood:
          features['onDefense'] = 0
          rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
          if action == rev:
            features['reverse'] = 1
        features['targetDistance'] = self.getMazeDistance(myPos, self.target)
  
    return features


  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'enemyDistance': -10, 'reverse': -10, 'targetDistance': -20}