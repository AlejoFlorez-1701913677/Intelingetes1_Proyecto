import argparse
import json
import random
import matplotlib.pyplot as plt
from mesa import Model, Agent
from mesa.time import RandomActivation



# Agente del modelo
class Persona(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.estado = "S"

    def step(self):
        if self.estado == "I":
            if random.random() < self.model.recovery_rate:
                self.estado = "R"
            else:
                vecinos = self.model.schedule.agents.copy()
                vecinos.remove(self)
                random.shuffle(vecinos)
                for agente in vecinos[:5]:
                    if agente.estado == "S" and random.random() < self.model.infection_rate:
                        agente.estado = "I"
        elif self.estado == "S":
            if random.random() < self.model.vaccination_rate:
                self.estado = "R"

# Modelo
class ContagioCityModel(Model):
    def __init__(self, N, infection_rate, recovery_rate, vaccination_rate):
        self.num_agents = N
        self.schedule = RandomActivation(self)
        self.infection_rate = infection_rate
        self.recovery_rate = recovery_rate
        self.vaccination_rate = vaccination_rate

        for i in range(self.num_agents):
            agente = Persona(i, self)
            if random.random() < 0.01:
                agente.estado = "I"
            self.schedule.add(agente)

    def step(self):
        self.schedule.step()

    def contar_estado(self, estado):
        return sum(1 for a in self.schedule.agents if a.estado == estado)

# CLI args
parser = argparse.ArgumentParser(description="Simulación Contagio City")
parser.add_argument('--population', type=int, default=1000)
parser.add_argument('--infection_rate', type=float, default=0.5)
parser.add_argument('--recovery_rate', type=float, default=0.001)
parser.add_argument('--vaccination_rate', type=float, default=0.005)
parser.add_argument('--steps', type=int, default=200)
args = parser.parse_args()

# Ejecutar simulación
model = ContagioCityModel(
    N=args.population,
    infection_rate=args.infection_rate,
    recovery_rate=args.recovery_rate,
    vaccination_rate=args.vaccination_rate
)

susceptibles = []
infectados = []
recuperados = []

for i in range(args.steps):
    model.step()
    susceptibles.append(model.contar_estado("S"))
    infectados.append(model.contar_estado("I"))
    recuperados.append(model.contar_estado("R"))

# Guardar datos JSON
resultado = {
    "population": args.population,
    "infection_rate": args.infection_rate,
    "recovery_rate": args.recovery_rate,
    "vaccination_rate": args.vaccination_rate,
    "steps": args.steps,
    "final_susceptibles": susceptibles[-1],
    "final_infectados": infectados[-1],
    "final_recuperados": recuperados[-1]
}

with open("C:/Users/AlejandroGonzales/Documents/Alejo/Universidad/2025-1/Inteligentes 1/Trabajos/Proyecto Entrega 1/Intelingetes1_Proyecto/src/code/Resultados/contagio_resultado.json", "w") as f:
    json.dump(resultado, f)

# Graficar resultados
plt.figure(figsize=(10, 6))
plt.plot(susceptibles, label='Susceptibles')
plt.plot(infectados, label='Infectados')
plt.plot(recuperados, label='Recuperados')
plt.xlabel("Tiempos")
plt.ylabel("Agentes")
plt.title("Evolución epidemiológica - Contagio City")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("C:/Users/AlejandroGonzales/Documents/Alejo/Universidad/2025-1/Inteligentes 1/Trabajos/Proyecto Entrega 1/Intelingetes1_Proyecto/src/code/Resultados/contagio_grafica.png")
plt.show()