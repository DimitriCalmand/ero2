"""
Module Regulation - Régulation et Hétérogénéité
Étudiant 4: Régulation & Hétérogénéité (Scénario Channels)

Ce module implémente:
- Gestion des populations multiples (ING vs PREPA)
- Gating (barrage temporel)
- Files prioritaires (SJF - Shortest Job First)
- Analyse de l'impact de l'hétérogénéité
"""

import simpy
import random
from typing import Optional, List, Callable
from collections import deque
from src.core.simulation_engine import SimulationLogger, EventType, Job


class PriorityQueue:
    """
    File d'attente avec gestion de priorités
    """
    
    def __init__(self):
        self.queue: List[Job] = []
    
    def add(self, job: Job):
        """Ajoute un job dans la file"""
        self.queue.append(job)
    
    def get_next_fifo(self) -> Optional[Job]:
        """Récupère le prochain job en FIFO"""
        if len(self.queue) == 0:
            return None
        return self.queue.pop(0)
    
    def get_next_sjf(self) -> Optional[Job]:
        """
        Récupère le prochain job selon Shortest Job First
        Suppose que job.service_time est déjà défini
        """
        if len(self.queue) == 0:
            return None
        
        # Trouve le job avec le temps de service minimal
        min_idx = 0
        min_time = self.queue[0].service_time if self.queue[0].service_time else float('inf')
        
        for i, job in enumerate(self.queue):
            job_time = job.service_time if job.service_time else float('inf')
            if job_time < min_time:
                min_time = job_time
                min_idx = i
        
        return self.queue.pop(min_idx)
    
    def get_next_priority(self, priority_order: List[str]) -> Optional[Job]:
        """
        Récupère le prochain job selon un ordre de priorité des types
        
        Args:
            priority_order: Liste des types par ordre de priorité (ex: ["ING", "PREPA"])
        """
        if len(self.queue) == 0:
            return None
        
        # Cherche d'abord dans l'ordre de priorité
        for job_type in priority_order:
            for i, job in enumerate(self.queue):
                if job.job_type == job_type:
                    return self.queue.pop(i)
        
        # Si aucun job trouvé dans les priorités, prend le premier
        return self.queue.pop(0)
    
    def __len__(self):
        return len(self.queue)


class GatingController:
    """
    Contrôleur de Gating (barrage temporel)
    Empêche l'accès au système pendant certaines périodes
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 gating_intervals: List[tuple]):
        """
        Args:
            env: Environnement SimPy
            gating_intervals: Liste de tuples (start_time, end_time) pour les périodes fermées
        """
        self.env = env
        self.gating_intervals = gating_intervals
    
    def is_open(self, time: Optional[float] = None) -> bool:
        """
        Vérifie si le système est ouvert
        
        Args:
            time: Temps à vérifier (utilise env.now si None)
            
        Returns:
            True si le système est ouvert
        """
        check_time = time if time is not None else self.env.now
        
        for start, end in self.gating_intervals:
            if start <= check_time < end:
                return False  # Fermé pendant cet intervalle
        
        return True
    
    def wait_until_open(self):
        """
        Processus d'attente jusqu'à l'ouverture du système
        """
        while not self.is_open():
            # Trouve le prochain temps d'ouverture
            next_open = None
            current_time = self.env.now
            
            for start, end in self.gating_intervals:
                if start <= current_time < end:
                    next_open = end
                    break
            
            if next_open:
                wait_time = next_open - current_time
                yield self.env.timeout(wait_time)
            else:
                break


class HeterogeneousServer:
    """
    Serveur gérant plusieurs populations avec caractéristiques différentes
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 server_id: str,
                 num_servers: int,
                 logger: SimulationLogger,
                 scheduling_policy: str = "FIFO",
                 gating_controller: Optional[GatingController] = None):
        """
        Args:
            env: Environnement SimPy
            server_id: Identifiant du serveur
            num_servers: Nombre de serveurs en parallèle
            logger: Logger centralisé
            scheduling_policy: Politique d'ordonnancement ("FIFO", "SJF", "PRIORITY")
            gating_controller: Contrôleur de gating optionnel
        """
        self.env = env
        self.server_id = server_id
        self.num_servers = num_servers
        self.resource = simpy.Resource(env, capacity=num_servers)
        self.logger = logger
        self.scheduling_policy = scheduling_policy
        self.gating_controller = gating_controller
        
        # File d'attente personnalisée
        self.custom_queue = PriorityQueue()
        
        # Statistiques par type de job
        self.stats_by_type = {}
    
    def _update_stats(self, job: Job, event: str):
        """Met à jour les statistiques pour un type de job"""
        if job.job_type not in self.stats_by_type:
            self.stats_by_type[job.job_type] = {
                'arrivals': 0,
                'completed': 0,
                'rejected': 0,
                'total_waiting_time': 0.0,
                'total_service_time': 0.0,
                'total_response_time': 0.0
            }
        
        stats = self.stats_by_type[job.job_type]
        
        if event == 'arrival':
            stats['arrivals'] += 1
        elif event == 'completed':
            stats['completed'] += 1
            if job.get_waiting_time():
                stats['total_waiting_time'] += job.get_waiting_time()
            if job.service_time:
                stats['total_service_time'] += job.service_time
            if job.get_response_time():
                stats['total_response_time'] += job.get_response_time()
        elif event == 'rejected':
            stats['rejected'] += 1
    
    def process_job(self, 
                   job: Job,
                   service_time_generator: Callable[[], float]):
        """
        Traite un job avec gestion du gating et de la priorité
        
        Args:
            job: Le job à traiter
            service_time_generator: Fonction générant le temps de service
        """
        # Vérification du gating
        if self.gating_controller and not self.gating_controller.is_open():
            # Attente de l'ouverture
            yield self.env.process(self.gating_controller.wait_until_open())
        
        # Enregistrement de l'arrivée
        self._update_stats(job, 'arrival')
        
        self.logger.log_event(
            time=self.env.now,
            event_type=EventType.ARRIVAL,
            entity_id=job.id,
            entity_type=job.job_type,
            server_id=self.server_id,
            queue_length=len(self.custom_queue)
        )
        
        # Génération du temps de service pour SJF
        service_time = service_time_generator()
        job.service_time = service_time
        
        # Ajout à la file personnalisée
        self.custom_queue.add(job)
        
        # Attente du serveur
        with self.resource.request() as request:
            yield request
            
            # Récupération du job selon la politique
            if self.scheduling_policy == "SJF":
                current_job = self.custom_queue.get_next_sjf()
            elif self.scheduling_policy == "PRIORITY":
                current_job = self.custom_queue.get_next_priority(["ING", "PREPA"])
            else:  # FIFO par défaut
                current_job = self.custom_queue.get_next_fifo()
            
            if current_job is None:
                return
            
            # Début du service
            current_job.start_time = self.env.now
            current_job.server_id = self.server_id
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=current_job.id,
                entity_type=current_job.job_type,
                server_id=self.server_id,
                queue_length=len(self.custom_queue),
                extra_data={
                    'scheduling_policy': self.scheduling_policy,
                    'service_time': current_job.service_time
                }
            )
            
            # Exécution du service
            yield self.env.timeout(current_job.service_time)
            
            # Fin du service
            current_job.end_time = self.env.now
            self._update_stats(current_job, 'completed')
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=current_job.id,
                entity_type=current_job.job_type,
                server_id=self.server_id,
                queue_length=len(self.custom_queue),
                extra_data={
                    'service_time': current_job.service_time,
                    'waiting_time': current_job.get_waiting_time(),
                    'response_time': current_job.get_response_time()
                }
            )
    
    def get_stats(self) -> dict:
        """Retourne les statistiques par type de job"""
        result = {
            'server_id': self.server_id,
            'scheduling_policy': self.scheduling_policy,
            'by_type': {}
        }
        
        for job_type, stats in self.stats_by_type.items():
            completed = stats['completed']
            result['by_type'][job_type] = {
                'arrivals': stats['arrivals'],
                'completed': completed,
                'rejected': stats['rejected'],
                'avg_waiting_time': stats['total_waiting_time'] / completed if completed > 0 else 0.0,
                'avg_service_time': stats['total_service_time'] / completed if completed > 0 else 0.0,
                'avg_response_time': stats['total_response_time'] / completed if completed > 0 else 0.0
            }
        
        return result


class PopulationGenerator:
    """
    Générateur pour une population spécifique (ING ou PREPA)
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 population_type: str,
                 arrival_rate: float,
                 service_rate: float):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            population_type: Type de population ("ING" ou "PREPA")
            arrival_rate: Taux d'arrivée λ
            service_rate: Taux de service μ
        """
        self.env = env
        self.logger = logger
        self.population_type = population_type
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.jobs_generated = 0
    
    def generate(self, server: HeterogeneousServer, duration: float):
        """
        Génère des jobs pour cette population
        
        Args:
            server: Serveur qui traitera les jobs
            duration: Durée de la simulation
        """
        def service_time_gen():
            return random.expovariate(self.service_rate)
        
        while self.env.now < duration:
            # Temps inter-arrivée
            interarrival = random.expovariate(self.arrival_rate)
            yield self.env.timeout(interarrival)
            
            if self.env.now >= duration:
                break
            
            # Création du job
            job = Job(
                arrival_time=self.env.now,
                job_type=self.population_type,
                assignment=f"{self.population_type}_{self.jobs_generated}"
            )
            self.jobs_generated += 1
            
            # Traitement
            self.env.process(server.process_job(job, service_time_gen))


class ChannelsScenario:
    """
    Scénario complet avec plusieurs populations et stratégies de régulation
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 num_servers: int,
                 scheduling_policy: str = "FIFO",
                 use_gating: bool = False,
                 gating_intervals: Optional[List[tuple]] = None):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            num_servers: Nombre de serveurs
            scheduling_policy: Politique d'ordonnancement
            use_gating: Activer le gating
            gating_intervals: Intervalles de fermeture
        """
        self.env = env
        self.logger = logger
        
        # Gating controller
        gating_controller = None
        if use_gating and gating_intervals:
            gating_controller = GatingController(env, gating_intervals)
        
        # Serveur hétérogène
        self.server = HeterogeneousServer(
            env=env,
            server_id="channels_server",
            num_servers=num_servers,
            logger=logger,
            scheduling_policy=scheduling_policy,
            gating_controller=gating_controller
        )
        
        self.populations = {}
    
    def add_population(self,
                      population_type: str,
                      arrival_rate: float,
                      service_rate: float):
        """
        Ajoute une population
        
        Args:
            population_type: Type de population
            arrival_rate: Taux d'arrivée
            service_rate: Taux de service
        """
        gen = PopulationGenerator(
            env=self.env,
            logger=self.logger,
            population_type=population_type,
            arrival_rate=arrival_rate,
            service_rate=service_rate
        )
        self.populations[population_type] = gen
    
    def run(self, duration: float) -> dict:
        """
        Exécute le scénario
        
        Args:
            duration: Durée de la simulation
            
        Returns:
            Statistiques par population
        """
        # Lancement des générateurs
        for pop_type, generator in self.populations.items():
            self.env.process(generator.generate(self.server, duration))
        
        # Exécution
        self.env.run(until=duration)
        
        # Résultats
        return self.server.get_stats()
