import random
import time

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

    def step(self):
        # Usamos los vecinos de la posición actual considerando las diagonales
        next_moves = self.model.grid.get_neighborhood(self.pos, moore=False)
        # Seleccionamos alguno de los vecinos de forma aleatoria y nos movemos a él
        next_move = self.random.choice(next_moves)

        # Se guarda la lista de los agentes que se encuentran en la posición a la que se quiere dirigir el robot
        angentsList = self.model.grid.get_cell_list_contents(next_move)

        # Iteramos por cada agente
        for agent in angentsList:
            # Si dicho agente es una celda sucia, la limpiamos removiendo el dicho agente
            if(str(type(agent).__name__) == "Box"):
                self.model.grid.remove_agent(agent)
                break

        # Movemos el robot a su nueva posición
        self.model.grid.move_agent(self, next_move)

        # Aumentamos el total de movimientos de los robots
        self.model.totalMovimientos += 1
        

# Usamos esta clase para crear las celdas sucias (las identificamos como agentes sin movimiento) 
class Box(Agent):
     def __init__(self, model, pos):
        super().__init__(model.next_id(), model)
        self.pos = pos

class Floor(Model):
    # Declaramos estos como atributos de la clase para poder usarlos en las demás clases que 
    # tengan acceso al modelo
    totalTime = 0
    totalMovimientos = 0
    boxStacks = {}
    stacksCompleted = 0

    def __init__(self):
        super().__init__()
        self.schedule = RandomActivation(self)

        # Establecemos el tamaño del Grid de 20x20
        self.x = 20
        self.y = 20

        # Declaramos la cantidad de Robots, la cuál está establecida en las instrucciones de la actividad
        cantRobots = 5
        # Declaramos el número de cajas en nuestro Grid
        cantBoxes = 15

        # Usamos un MultiGrid para poder colocar múltiples agentes en una misma celda
        self.grid = MultiGrid(self.x, self.y, torus=False)

        # Declaramos nuestras variables que ingresará el usuario desde el input
        self.startTime = 0
        
        # Establecemos que el tiempo máximo de la simulación sea de 30 segundos
        self.maxTime = 30

        # Cuando el counter haya aumentado (es decir, después de la primera llamada al constructor) se pueden pedir los datos de porcentaje de basura, número de Robots y tiempo máximo  
        self.startTime = time.time()

        # Reiniciamos el conteo de movimientos en cada llamada al constructor
        self.totalMovimientos = 0

        # Creamos una lista con números aleatorios en el rango de la basura que desea el usuario
        randomNumsList = random.sample(range(self.x*self.y), cantBoxes)

        # Insertamos la basura iterativamente en posiciones aleatorias
        for i in randomNumsList:
          posY = i // self.x
          posX = i % self.x
          # llamamos a la clase Box y la instanciamos con las coordenadas de la matriz declarada.
          box = Box(self, (posX, posY))
          # enviamos como parametro a la clase place_agent para que se muestre en el navegador
          self.grid.place_agent(box, box.pos)
          
        # Creamos los robots necesarios
        for _ in range(cantRobots):
          gh = Robot(self, (1, 1))
          self.grid.place_agent(gh, gh.pos)
          self.schedule.add(gh)

    def step(self):
        self.schedule.step()        

        # Si el tiempo actual sobrepasa el tiempo en el que debe terminar la simulación, se detiene la simulación
        if(self.startTime + self.maxTime < time.time() or self.stacksCompleted == 3):
            self.running = False
            
            # Calculamos el tiempo que duró la simulación
            self.totalTime = round(time.time() - self.startTime)

# creamos la clase de TextResults, la cual nos devuelve una serie de etiquetas de texto con los resultados obtenidos durante y al final de la simulación. 
# haciendo uso de HTML podemos colocar las etiquetas en nuestra aplicación con ayuda de etiquetas como <br> y <hr> para tener una mejor organización. 
class TextResults(TextElement):
    def render(self, model):
        return f"""
            <br>Tiempo necesario hasta que todas las celdas estén limpias (o se haya llegado al tiempo máximo): <b>{model.totalTime} segundos </b>
            <hr>
            Número de movimientos realizados por todos los agentes: <b>{model.totalMovimientos} movimientos</b>
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
server = ModularServer(Floor, [grid, TextResults()], "Robots Apiladores", {})
server.port = 8573
server.launch()