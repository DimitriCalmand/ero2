"""
Module Core - Architecture de Base et Moteur de Simulation
Étudiant 1: Architecture Core & Moteur

Ce module fournit:
- Gestion du temps simulé avec SimPy
- Classes de base pour les générateurs et serveurs
- Système de logging centralisé pour l'analyse
"""

import simpy
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class EventType(Enum):
    """Types d'événements dans la simulation"""
    ARRIVAL = "arrival"
    START_SERVICE = "start_service"
    END_SERVICE = "end_service"
    REJECTION = "rejection"
    BACKUP_START = "backup_start"
    BACKUP_END = "backup_end"


class SimulationLogger:
    """
    Système de logging centralisé pour collecter tous les événements
    de la simulation et générer des DataFrames pour l'analyse.
    """
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        
    def log_event(self, 
                  time: float,
                  event_type: EventType,
                  entity_id: int,
                  entity_type: str,
                  server_id: Optional[str] = None,
                  queue_length: Optional[int] = None,
                  extra_data: Optional[Dict[str, Any]] = None):
        """
        Enregistre un événement dans le log
        
        Args:
            time: Temps simulé de l'événement
            event_type: Type d'événement
            entity_id: ID de l'entité (push/job)
            entity_type: Type d'entité (ING/PREPA)
            server_id: ID du serveur concerné
            queue_length: Longueur de la file au moment de l'événement
            extra_data: Données supplémentaires spécifiques
        """
        event = {
            'time': time,
            'event_type': event_type.value,
            'entity_id': entity_id,
            'entity_type': entity_type,
            'server_id': server_id,
            'queue_length': queue_length,
            'timestamp': datetime.now()
        }
        
        if extra_data:
            event.update(extra_data)
            
        self.events.append(event)
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Retourne tous les événements sous forme de DataFrame
        """
        return pd.DataFrame(self.events)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé statistique des événements
        """
        df = self.get_dataframe()
        if df.empty:
            return {}
        
        summary = {
            'total_events': len(df),
            'total_arrivals': len(df[df['event_type'] == EventType.ARRIVAL.value]),
            'total_rejections': len(df[df['event_type'] == EventType.REJECTION.value]),
            'total_completed': len(df[df['event_type'] == EventType.END_SERVICE.value]),
            'simulation_duration': df['time'].max() if len(df) > 0 else 0
        }
        
        return summary
    
    def clear(self):
        """Efface tous les événements"""
        self.events.clear()


class Job:
    """
    Représente une soumission (git push) dans le système
    """
    
    _id_counter = 0
    
    def __init__(self, 
                 arrival_time: float,
                 job_type: str = "ING",
                 assignment: str = "generic"):
        """
        Args:
            arrival_time: Temps d'arrivée dans le système
            job_type: Type de job (ING ou PREPA)
            assignment: Nom de l'assignment
        """
        self.id = Job._id_counter
        Job._id_counter += 1
        
        self.arrival_time = arrival_time
        self.job_type = job_type
        self.assignment = assignment
        
        # Temps de traitement (sera défini par le serveur)
        self.service_time: Optional[float] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Métadonnées
        self.was_rejected = False
        self.rejection_reason: Optional[str] = None
        self.server_id: Optional[str] = None
    
    def get_waiting_time(self) -> Optional[float]:
        """Retourne le temps d'attente"""
        if self.start_time is None:
            return None
        return self.start_time - self.arrival_time
    
    def get_response_time(self) -> Optional[float]:
        """Retourne le temps de réponse total (attente + service)"""
        if self.end_time is None:
            return None
        return self.end_time - self.arrival_time
    
    def __repr__(self):
        return f"Job(id={self.id}, type={self.job_type}, arrival={self.arrival_time:.2f})"


class Server:
    """
    Représente un serveur de traitement (avec capacité limitée)
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 server_id: str,
                 num_servers: int,
                 logger: SimulationLogger):
        """
        Args:
            env: Environnement SimPy
            server_id: Identifiant unique du serveur
            num_servers: Nombre de serveurs en parallèle (capacité)
            logger: Logger centralisé
        """
        self.env = env
        self.server_id = server_id
        self.resource = simpy.Resource(env, capacity=num_servers)
        self.logger = logger
        
        # Statistiques
        self.jobs_processed = 0
        self.total_service_time = 0.0
    
    def process(self, job: Job, service_time_generator):
        """
        Traite un job
        
        Args:
            job: Le job à traiter
            service_time_generator: Fonction qui génère le temps de service
        """
        # Demande d'accès au serveur
        with self.resource.request() as request:
            yield request
            
            # Début du service
            job.start_time = self.env.now
            job.server_id = self.server_id
            service_time = service_time_generator()
            job.service_time = service_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.server_id,
                queue_length=len(self.resource.queue)
            )
            
            # Attente du temps de service
            yield self.env.timeout(service_time)
            
            # Fin du service
            job.end_time = self.env.now
            self.jobs_processed += 1
            self.total_service_time += service_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.server_id,
                queue_length=len(self.resource.queue),
                extra_data={
                    'service_time': service_time,
                    'waiting_time': job.get_waiting_time(),
                    'response_time': job.get_response_time()
                }
            )
    
    def get_utilization(self, simulation_time: float) -> float:
        """
        Calcule le taux d'utilisation du serveur
        """
        if simulation_time == 0:
            return 0.0
        return self.total_service_time / simulation_time


class JobGenerator:
    """
    Générateur de jobs selon un processus de Poisson
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 arrival_rate: float,
                 job_type: str = "ING"):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            arrival_rate: Taux d'arrivée λ (jobs par unité de temps)
            job_type: Type de jobs générés (ING ou PREPA)
        """
        self.env = env
        self.logger = logger
        self.arrival_rate = arrival_rate
        self.job_type = job_type
        self.jobs_generated = 0
    
    def generate(self, server: Server, service_time_generator, duration: float):
        """
        Processus de génération de jobs
        
        Args:
            server: Serveur qui traitera les jobs
            service_time_generator: Fonction qui génère les temps de service
            duration: Durée de la simulation
        """
        import random
        
        while self.env.now < duration:
            # Temps inter-arrivée exponentiel
            interarrival_time = random.expovariate(self.arrival_rate)
            yield self.env.timeout(interarrival_time)
            
            if self.env.now >= duration:
                break
            
            # Création d'un nouveau job
            job = Job(
                arrival_time=self.env.now,
                job_type=self.job_type,
                assignment=f"assignment_{self.jobs_generated}"
            )
            self.jobs_generated += 1
            
            # Log de l'arrivée
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.ARRIVAL,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=server.server_id,
                queue_length=len(server.resource.queue)
            )
            
            # Démarrage du traitement
            self.env.process(server.process(job, service_time_generator))


class SimulationEngine:
    """
    Moteur principal de simulation
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """
        Args:
            random_seed: Graine pour la reproductibilité
        """
        self.env = simpy.Environment()
        self.logger = SimulationLogger()
        self.random_seed = random_seed
        
        if random_seed is not None:
            import random
            random.seed(random_seed)
    
    def run(self, duration: float):
        """
        Lance la simulation
        
        Args:
            duration: Durée de la simulation
        """
        self.env.run(until=duration)
    
    def get_results(self) -> pd.DataFrame:
        """
        Récupère les résultats de la simulation
        """
        return self.logger.get_dataframe()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des résultats
        """
        return self.logger.get_summary()
    
    def reset(self):
        """
        Réinitialise la simulation
        """
        self.env = simpy.Environment()
        self.logger.clear()
        Job._id_counter = 0
        
        if self.random_seed is not None:
            import random
            random.seed(self.random_seed)
