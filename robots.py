import random
import time
import math

from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import TextElement
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

class Robot(Agent):
    def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.myBox = None # Atributo que guarda una caja (agent) en caso de haberla levantado
        self.closestStackPos = (-1,-1) # Atributo que guarda la posición de la stack más cercana
        self.lastPos = self.pos

    def step(self):
        # Usamos los vecinos de la posición actual considerando las diagonales
        next_moves = self.model.grid.get_neighborhood(self.pos, moore=False)
        # Seleccionamos alguno de los vecinos de forma aleatoria y nos movemos a él
        
        # It has to select a neighbor that is not a stack/robot/box
        next_move = self.getMove(next_moves)

        # Movemos el robot a su nueva posición
        self.model.grid.move_agent(self, next_move)

        # Aumentamos el total de movimientos de los robots
        self.model.totalMoves += 1

    def getMove(self, next_moves):
        # Si no han sido creadas las stacks suficientes, creamos otra con esa caja (en su posición actual)

        if(self.myBox == None):
            posibleMoves = []
            for move in next_moves:
                
                angentsList = self.model.grid.get_cell_list_contents(move)
                if(len(angentsList) == 0):
                    posibleMoves.append(move)
                for agent in angentsList:
                    # Si la casilla vecina tiene una caja, la recojemos
                    if(str(type(agent).__name__) == "Box" and not agent.wasTaken):
                        self.myBox = agent
                        agent.wasTaken = True
                        # self.model.grid.remove_agent(agent)
                        return move
            try:
                posibleMoves.remove(self.lastPos)
            except:
                '''It was not possible to move to the lastPos'''

            self.lastPos = self.pos

            if(len(posibleMoves) == 0):
                self.model.totalMoves -= 1
                return self.pos
            
            return self.random.choice(posibleMoves)
        
        else:
            if(len(self.model.boxStacks) < self.model.amountStacks):
                self.model.boxStacks[self.myBox.pos] = 1
                self.myBox.isStacked = True
                self.myBox = None
                self.model.boxesStacked += 1
                return self.random.choice(next_moves)
            
            else:
                # La función nos regresa la posición de la stack más cercana a nuestra box
                if(self.closestStackPos[0] == -1 or (self.closestStackPos in self.model.boxStacks and self.model.boxStacks[self.closestStackPos] >= 5)):
                    self.closestStackPos = self.findStack()
                
                bestMove = [10000.0, (0,0)]
                for move in next_moves:
                    # Comprobamos que no se quiera pasar sobre una caja o robot
                    if not (move != self.closestStackPos and len(self.model.grid.get_cell_list_contents(move)) > 0):
                        distanceTmp = math.sqrt((self.closestStackPos[0]-move[0])**2 + (self.closestStackPos[1]-move[1])**2)
                        if(distanceTmp < bestMove[0]):
                            bestMove = [distanceTmp, move]

                # Si el siguiente mejor movimiento es la stack que buscamos, ponemos allí la caja y nos olvidamos de ella
                if(bestMove[0] == 0):
                    # Ponemos la caja y actiualizamos sus valores
                    self.model.grid.move_agent(self.myBox, bestMove[1])
                    self.myBox.isStacked = True
                    
                    # Sumamos 1 elemento a dicha stack
                    self.model.boxStacks[bestMove[1]] += 1
                    # Aumentamos el número de cajas en stacks
                    self.model.boxesStacked += 1
                    
                    # Reestablecemos la posición del stack más cercano y nos quitamos la caja
                    self.closestStackPos = (-1,-1)
                    self.myBox = None

                    self.model.totalMoves -= 1
                    return self.pos
                
                return bestMove[1]

    # Buscamos la stack más cercana a dicha caja
    def findStack(self):
        minDistance = [10000.0, (0,0)]
        distanceTmp = 0.0
        for pos, cant in self.model.boxStacks.items():
            if(cant < 5):
                # Cálculo de la distancia entre los dos puntos
                distanceTmp = math.sqrt((pos[0]-self.myBox.pos[0])**2 + (pos[1]-self.myBox.pos[1])**2)
                if(distanceTmp < minDistance[0]):
                    minDistance = [distanceTmp, pos]
        
        return minDistance[1]
            

# Usamos esta clase para crear las celdas sucias (las identificamos como agentes sin movimiento) 
class Box(Agent):
     def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos
        self.wasTaken = False
        self.isStacked = False

class Floor(Model):

    def __init__(self, cantidadCajas = 15, tiempoMaximo = 30):
        super().__init__()
        self.schedule = RandomActivation(self)

        # Establecemos el tamaño del Grid de 20x20
        self.x = 20
        self.y = 20

        # Creamos el diccionario que guardará en su key la posición de la stack y en su value la cantidad de cajas que tiene dicha stack
        self.boxStacks = {}
        # También creamos la variable que indicará la cantidad de cajas que se han metido en una stack
        self.boxesStacked = 0

        # Declaramos la cantidad de Robots, la cuál está establecida en las instrucciones de la actividad
        amountRobots = 5
        # Declaramos el número de cajas en nuestro Grid como atributo de nuestra clase
        self.amountBoxes = cantidadCajas

        # Calculamos la cantidad de stacks necesarias para el número de cajas ingresado
        self.amountStacks = self.amountBoxes // amountRobots + (0 if self.amountBoxes%amountRobots == 0 else 1)

        # Usamos un MultiGrid para poder colocar múltiples agentes en una misma celda
        self.grid = MultiGrid(self.x, self.y, torus=False)

        # Variable tipo flag que será True cuando se ejecute el primer step de la simulación
        self.simulationStarted = False

        # Atributo que indica el tiempo en el que inicia la simulación
        self.startTime = 0

        # Establecemos que el tiempo máximo de la simulación sea de 30 segundos
        self.maxTime = tiempoMaximo

        # Declaramos la variable que nos indica el tiempo actual que lleva la simulación
        self.actualTime = 0

        # Reiniciamos el conteo de movimientos en cada llamada al constructor
        self.totalMoves = 0

        # Creamos una lista con números aleatorios en el rango de la basura que desea el usuario
        randomNumsList = random.sample(range(self.x*self.y), self.amountBoxes + amountRobots)

        count = 0
        # Insertamos la basura iterativamente en posiciones aleatorias
        for i in randomNumsList:
            posY = i // self.x
            posX = i % self.x
            # Primero creamos los 5 robots
            if(count < amountRobots):
                robot = Robot(self, (posX, posY))
                self.grid.place_agent(robot, robot.pos)
                self.schedule.add(robot)
                count += 1
            else:
                # llamamos a la clase Box y la instanciamos con las coordenadas de la matriz declarada.
                box = Box(self, (posX, posY))
                # enviamos como parametro a la clase place_agent para que se muestre en el navegador
                self.grid.place_agent(box, box.pos)
          

    def step(self):
        if(not self.simulationStarted):
            # Declaramos el tiempo de inicio del tiempo como ahora 
            self.startTime = time.time()
            self.simulationStarted = True
        self.schedule.step()        
        self.actualTime = round(time.time() - self.startTime)

        # Si el tiempo actual sobrepasa el tiempo en el que debe terminar la simulación, se detiene la simulación
        if(self.startTime + self.maxTime < time.time() or self.boxesStacked == self.amountBoxes):
            self.running = False
            
# creamos la clase de TextResults, la cual nos devuelve una serie de etiquetas de texto con los resultados obtenidos durante y al final de la simulación. 
# haciendo uso de HTML podemos colocar las etiquetas en nuestra aplicación con ayuda de etiquetas como <br> y <hr> para tener una mejor organización. 
class TextResults(TextElement):
    def render(self, model):
        return f"""
            <br>Tiempo que lleva la simulación: <b>{model.actualTime} segundos </b>
            <hr>
            Número de movimientos realizados por todos los agentes: <b>{model.totalMoves} movimientos</b>
        """

def agent_portrayal(agent):
    # si el tipo de clase recibido es Box, retornamos un muro
    if str(type(agent).__name__) == "Box":
         return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "Gray", "Layer": 0}
    # sino retornamos una imagen
    return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "Blue", "Layer": 0}

# Establecemos el tamaño del CanvasGrid que sea de 20*20 celdas
grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Hacemos uso de la funcion de UserSettableParameter, la cual nos da una serie de widgets que nos permiten tener una mejor interacción con la simulación a traves de sliders, inputs de texto, entre otros, lo que nos permite manipuilar facilmente los valores iniciales.
server = ModularServer(Floor, [grid, TextResults()], "Robots Apiladores", {
    # A traves de un drop down box para ingresar el total de robots.
    "cantidadCajas": UserSettableParameter("number", "Número de cajas", value=15), 

    # A traves de un drop down box para ingresar el la duracion máxima.
    "tiempoMaximo": UserSettableParameter("number", "Tiempo máximo de simulación (segundos)", value=30),
})
server.port = 8573
server.launch()