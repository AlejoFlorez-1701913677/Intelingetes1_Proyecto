from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter, StaticText

import random

# Estados
SUSCEPTIBLE = "Susceptible"
INFECTADO = "Infectado"
RECUPERADO = "Recuperado"
MUERTO = "Muerto"

# Agente
class Ciudadano(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.estado = SUSCEPTIBLE
        self.tiempo_infeccion = 0
        self.variante = None
        self.usa_mascarilla = False
        self.vacunado = False

    def mover(self):
        if self.estado != MUERTO:
            vecinos = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            nueva_pos = self.random.choice(vecinos)
            self.model.grid.move_agent(self, nueva_pos)

    def infectar(self):
        vecinos = self.model.grid.get_cell_list_contents(self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False))

        for vecino in vecinos:
            if isinstance(vecino, Ciudadano) and vecino.estado == INFECTADO:
                # Reducción de contagio si uno o ambos usan mascarilla
                factor_mascarilla = 1.0
                if self.usa_mascarilla:
                    factor_mascarilla *= 0.5  # reduce 50%
                if vecino.usa_mascarilla:
                    factor_mascarilla *= 0.5  # reduce otro 50%
                
                prob_contagio = self.model.tasa_contagio * factor_mascarilla

                variante = vecino.variante
                #contagio = self.model.variantes[variante]["contagio"]
                
                if random.random() < (prob_contagio):# + contagio):
                    self.estado = INFECTADO
                    self.variante = variante

    def vacunar(self):
        # Vacunación basada en probabilidad
        if random.random() < self.model.probabilidad_vacunacion and self.estado == SUSCEPTIBLE:
            self.vacunado = True
            self.estado = RECUPERADO  # Asumimos que la vacunación previene el contagio
            
    def step(self):
        # Vacunación
        self.vacunar()
        if self.estado == SUSCEPTIBLE:
             # Asignar mascarilla en cada paso con base en la probabilidad
            if random.random() < self.model.probabilidad_uso_mascarilla:
                self.usa_mascarilla = True
            else:
                self.usa_mascarilla = False
            # Contagio
            self.infectar()
        elif self.estado == INFECTADO:
            self.tiempo_infeccion += 1

            # Mortalidad
            letalidad = self.model.variantes[self.variante]["letalidad"]
            if random.random() < letalidad:
                self.estado = MUERTO
                return

            if self.tiempo_infeccion >= self.model.duracion_infeccion:
                self.estado = RECUPERADO
        
        if self.estado != MUERTO:
            self.mover()

# Modelo
class EpidemiaModel(Model):
    def __init__(self, N, width, height, tasa_contagio, duracion_infeccion, probabilidad_uso_mascarilla, mostrar_muertos, probabilidad_vacunacion):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.tasa_contagio = tasa_contagio
        self.duracion_infeccion = duracion_infeccion
        self.probabilidad_uso_mascarilla = probabilidad_uso_mascarilla
        self.mostrar_muertos = mostrar_muertos
        self.probabilidad_vacunacion = probabilidad_vacunacion  # Nueva probabilidad de vacunación

        self.variantes = {
            "Original": {"contagio": 0.3, "letalidad": 0.01},
            "Variante X": {"contagio": 0.5, "letalidad": 0.02},
            "Variante Y": {"contagio": 0.4, "letalidad": 0.03},
        }

        self.variantes_lista = list(self.variantes.keys())
        self.virus_actual = "Original"
        self.mutacion_ciclo = 10

        for i in range(self.num_agents):
            a = Ciudadano(i, self)
            if i == 0:
                a.estado = INFECTADO  # Paciente cero
                a.variante = self.virus_actual
            self.schedule.add(a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "Susceptibles": lambda m: self.contar_estado(SUSCEPTIBLE),
                "Infectados": lambda m: self.contar_estado(INFECTADO),
                "Recuperados": lambda m: self.contar_estado(RECUPERADO),
                "Mascarilla": lambda m: sum(1 for a in m.schedule.agents if a.usa_mascarilla),
                "Vacunados": lambda m: sum(1 for a in m.schedule.agents if a.vacunado),
                "Muertos": lambda m: self.contar_estado(MUERTO),
                "Variante X": lambda m: sum(1 for a in m.schedule.agents if getattr(a, "variante", None) == "Variante X" and a.estado == INFECTADO),
                "Variante Y": lambda m: sum(1 for a in m.schedule.agents if getattr(a, "variante", None) == "Variante Y" and a.estado == INFECTADO),
                "Susceptibles con Mascarilla": lambda m: sum(1 for a in m.schedule.agents if a.estado == SUSCEPTIBLE and a.usa_mascarilla),
                "Infectados con Mascarilla": lambda m: sum(1 for a in m.schedule.agents if a.estado == INFECTADO and a.usa_mascarilla)
            }
        )


    def contar_estado(self, estado):
        return sum(1 for a in self.schedule.agents if a.estado == estado)

    def step(self):

        # Mutación del virus
        if self.schedule.time == self.mutacion_ciclo:
            self.virus_actual = random.choice(self.variantes_lista[1:])
            print(f"⚠️ Mutación detectada: Variante activa ahora es {self.virus_actual}")

        self.datacollector.collect(self)
        self.schedule.step()

# Visualización: Representación por color
def agent_portrayal(agent):
    if agent.estado == SUSCEPTIBLE:
        if agent.usa_mascarilla:
            color = "purple"  # Susceptible con mascarilla
        else:
            color = "blue"  # Susceptible sin mascarilla
    elif agent.estado == INFECTADO:
        if agent.usa_mascarilla:
            color = "orange"  # Infectado con mascarilla
        else:
            color = "red"  # Infectado sin mascarilla
    elif agent.estado == RECUPERADO:
        color = "green"  # Recuperado
    elif agent.estado == MUERTO:
        color = "black"  # Muerto

    portrayal = {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "Layer": 0,
        "r": 0.7,
    }

    # Si el agente usa mascarilla, se agrega un borde rosa
    if agent.usa_mascarilla:
        portrayal["stroke_color"] = "pink"
        portrayal["stroke_width"] = 100  # Grosor del borde de la mascarilla

    return portrayal


# Configuración visual del grid
grid = CanvasGrid(agent_portrayal, 50, 50, 500, 500)

# Gráfica de evolución
chart = ChartModule(
    [
        {"Label": "Susceptibles", "Color": "blue"},
        {"Label": "Infectados", "Color": "red"},
        {"Label": "Recuperados", "Color": "green"},
        {"Label": "Muertos", "Color": "black"},
        {"Label": "Mascarilla", "Color": "pink"},
        {"Label": "Susceptibles con Mascarilla", "Color": "purple"},
        {"Label": "Infectados con Mascarilla", "Color": "orange"},
        {"Label": "Vacunados", "Color": "cyan"},
        {"Label": "Variante X", "Color": "orange"},
        {"Label": "Variante Y", "Color": "purple"}
    ],
    data_collector_name='datacollector'
)

# Interfaz con parámetros modificables
server = ModularServer(
    EpidemiaModel,
    [grid, chart],
    "Simulación de Epidemia - Contagio City",
    {
        "width": 50,
        "height": 50,
        "N": UserSettableParameter("slider", "Cantidad de agentes", 1000, 10, 1000, 10),
        "tasa_contagio": UserSettableParameter("slider", "Tasa de contagio", 5, 0.0, 35, 0.05),
        "duracion_infeccion": UserSettableParameter("slider", "Duración de infección", 10, 1, 50, 1),
        "probabilidad_uso_mascarilla": UserSettableParameter("slider", "Probabilidad de uso de mascarilla", 0.5, 0.0, 1.0, 0.05),
        "probabilidad_vacunacion": UserSettableParameter("slider", "Probabilidad de vacunación", 0.5, 0.0, 1.0, 0.05),
        "mostrar_muertos": UserSettableParameter("checkbox", "Mostrar ciudadanos muertos", True),

    }
)

# Ejecutar servidor
if __name__ == "__main__":
    server.port = 8521
    server.launch(open_browser=False)
