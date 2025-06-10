from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
import random

# Estados
SUSCEPTIBLE = "Susceptible"
INFECTADO = "Infectado"
RECUPERADO = "Recuperado"

# Agente
class Ciudadano(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.estado = SUSCEPTIBLE
        self.tiempo_infeccion = 0

    def mover(self):
        vecinos = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        nueva_pos = self.random.choice(vecinos)
        self.model.grid.move_agent(self, nueva_pos)

    def infectar(self):
        vecinos = self.model.grid.get_cell_list_contents(
            self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        )
        for vecino in vecinos:
            if isinstance(vecino, Ciudadano) and vecino.estado == INFECTADO:
                if random.random() < self.model.tasa_contagio:
                    self.estado = INFECTADO

    def step(self):
        if self.estado == SUSCEPTIBLE:
            self.infectar()
        elif self.estado == INFECTADO:
            self.tiempo_infeccion += 1
            if self.tiempo_infeccion >= self.model.duracion_infeccion:
                self.estado = RECUPERADO
        self.mover()

# Modelo
class EpidemiaModel(Model):
    def __init__(self, N, width, height, tasa_contagio, duracion_infeccion):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.tasa_contagio = tasa_contagio
        self.duracion_infeccion = duracion_infeccion

        for i in range(self.num_agents):
            a = Ciudadano(i, self)
            if i == 0:
                a.estado = INFECTADO  # Paciente cero
            self.schedule.add(a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "Susceptibles": lambda m: self.contar_estado(SUSCEPTIBLE),
                "Infectados": lambda m: self.contar_estado(INFECTADO),
                "Recuperados": lambda m: self.contar_estado(RECUPERADO),
            }
        )

    def contar_estado(self, estado):
        return sum(1 for a in self.schedule.agents if a.estado == estado)

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

# Visualización: Representación por color
def agent_portrayal(agent):
    if agent.estado == SUSCEPTIBLE:
        color = "blue"
    elif agent.estado == INFECTADO:
        color = "red"
    elif agent.estado == RECUPERADO:
        color = "green"

    return {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "Layer": 0,
        "r": 0.5,
    }

# Configuración visual del grid
grid = CanvasGrid(agent_portrayal, 50, 50, 500, 500)

# Gráfica de evolución
chart = ChartModule(
    [
        {"Label": "Susceptibles", "Color": "blue"},
        {"Label": "Infectados", "Color": "red"},
        {"Label": "Recuperados", "Color": "green"},
    ]
)

# Interfaz con parámetros modificables
server = ModularServer(
    EpidemiaModel,
    [grid, chart],
    "Simulación de Epidemia - Contagio City",
    {
        "N": UserSettableParameter("slider", "Cantidad de agentes", 1000, 10, 1000, 10),
        "width": 50,
        "height": 50,
        "tasa_contagio": UserSettableParameter("slider", "Tasa de contagio", 0.3, 0.0, 35, 0.05),
        "duracion_infeccion": UserSettableParameter("slider", "Duración de infección", 10, 1, 50, 1),
    },
)

# Ejecutar servidor
if __name__ == "__main__":
    server.port = 8521
    server.launch()
