"""
Module Capacity - Gestion des Capacités et Files Finies
Étudiant 2: Gestion des Capacités (Scénario Waterfall)

Ce module implémente:
- Files finies avec capacités ks (serveurs) et kf (file d'attente)
- Logique de rejet (Loss System vs Queueing)
- Analyse des taux de rejet (Page Blanche vs Erreur immédiate)
"""

import simpy
from typing import Optional
from src.core.simulation_engine import SimulationLogger, EventType, Job


class LimitedQueue:
    """
    File d'attente avec capacité limitée
    """
    
    def __init__(self, 
                 env: simpy.Environment,
                 queue_id: str,
                 max_queue_size: int,
                 num_servers: int,
                 logger: SimulationLogger):
        """
        Args:
            env: Environnement SimPy
            queue_id: Identifiant de la file
            max_queue_size: Taille maximale de la file d'attente (kf)
            num_servers: Nombre de serveurs (ks)
            logger: Logger centralisé
        """
        self.env = env
        self.queue_id = queue_id
        self.max_queue_size = max_queue_size
        self.num_servers = num_servers
        self.logger = logger
        
        # Resource SimPy avec capacité limitée
        # Capacité totale = serveurs + file d'attente
        self.resource = simpy.Resource(env, capacity=num_servers)
        
        # Statistiques
        self.total_arrivals = 0
        self.total_rejections = 0
        self.rejections_queue_full = 0  # File pleine
        self.rejections_server_full = 0  # Serveurs pleins
        self.jobs_completed = 0
        
    def get_queue_length(self) -> int:
        """Retourne la longueur actuelle de la file"""
        return len(self.resource.queue)
    
    def get_total_in_system(self) -> int:
        """Retourne le nombre total d'entités dans le système"""
        return self.resource.count + len(self.resource.queue)
    
    def is_queue_full(self) -> bool:
        """Vérifie si la file d'attente est pleine"""
        return len(self.resource.queue) >= self.max_queue_size
    
    def is_server_full(self) -> bool:
        """Vérifie si tous les serveurs sont occupés"""
        return self.resource.count >= self.num_servers
    
    def process_job(self, job: Job, service_time_generator):
        """
        Traite un job avec gestion des capacités limitées
        
        Args:
            job: Le job à traiter
            service_time_generator: Fonction générant le temps de service
        """
        self.total_arrivals += 1
        
        # Vérification de la capacité AVANT d'entrer dans la file
        total_in_system = self.get_total_in_system()
        
        # Rejet si le système est plein (serveurs + file)
        if total_in_system >= (self.num_servers + self.max_queue_size):
            # Rejet - File d'attente pleine
            job.was_rejected = True
            job.rejection_reason = "queue_full"
            self.total_rejections += 1
            self.rejections_queue_full += 1
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.REJECTION,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.queue_id,
                queue_length=self.get_queue_length(),
                extra_data={
                    'rejection_reason': 'queue_full',
                    'total_in_system': total_in_system
                }
            )
            return
        
        # Tentative d'accès au serveur
        with self.resource.request() as request:
            yield request
            
            # Début du service
            job.start_time = self.env.now
            job.server_id = self.queue_id
            service_time = service_time_generator()
            job.service_time = service_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.queue_id,
                queue_length=self.get_queue_length()
            )
            
            # Exécution du service
            yield self.env.timeout(service_time)
            
            # Fin du service
            job.end_time = self.env.now
            self.jobs_completed += 1
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.queue_id,
                queue_length=self.get_queue_length(),
                extra_data={
                    'service_time': service_time,
                    'waiting_time': job.get_waiting_time(),
                    'response_time': job.get_response_time()
                }
            )
    
    def get_rejection_rate(self) -> float:
        """Calcule le taux de rejet"""
        if self.total_arrivals == 0:
            return 0.0
        return self.total_rejections / self.total_arrivals
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de la file"""
        return {
            'queue_id': self.queue_id,
            'total_arrivals': self.total_arrivals,
            'total_rejections': self.total_rejections,
            'rejections_queue_full': self.rejections_queue_full,
            'jobs_completed': self.jobs_completed,
            'rejection_rate': self.get_rejection_rate(),
            'completion_rate': self.jobs_completed / self.total_arrivals if self.total_arrivals > 0 else 0.0
        }


class LossSystem:
    """
    Système avec perte immédiate (pas de file d'attente)
    Rejet si tous les serveurs sont occupés
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 system_id: str,
                 num_servers: int,
                 logger: SimulationLogger):
        """
        Args:
            env: Environnement SimPy
            system_id: Identifiant du système
            num_servers: Nombre de serveurs (ks)
            logger: Logger centralisé
        """
        self.env = env
        self.system_id = system_id
        self.num_servers = num_servers
        self.logger = logger
        
        # Resource sans file d'attente (capacité = nombre de serveurs)
        self.resource = simpy.Resource(env, capacity=num_servers)
        
        # Statistiques
        self.total_arrivals = 0
        self.total_rejections = 0
        self.jobs_completed = 0
    
    def process_job(self, job: Job, service_time_generator):
        """
        Traite un job avec rejet immédiat si serveurs pleins
        
        Args:
            job: Le job à traiter
            service_time_generator: Fonction générant le temps de service
        """
        self.total_arrivals += 1
        
        # Vérification immédiate: serveurs disponibles?
        if self.resource.count >= self.num_servers:
            # Rejet immédiat - Erreur
            job.was_rejected = True
            job.rejection_reason = "servers_full"
            self.total_rejections += 1
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.REJECTION,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.system_id,
                queue_length=0,
                extra_data={
                    'rejection_reason': 'servers_full',
                    'servers_busy': self.resource.count
                }
            )
            return
        
        # Traitement normal
        with self.resource.request() as request:
            yield request
            
            job.start_time = self.env.now
            job.server_id = self.system_id
            service_time = service_time_generator()
            job.service_time = service_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.system_id,
                queue_length=0
            )
            
            yield self.env.timeout(service_time)
            
            job.end_time = self.env.now
            self.jobs_completed += 1
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.system_id,
                queue_length=0,
                extra_data={
                    'service_time': service_time,
                    'response_time': service_time  # Pas d'attente dans un Loss System
                }
            )
    
    def get_blocking_probability(self) -> float:
        """
        Calcule la probabilité de blocage (formule d'Erlang B)
        """
        if self.total_arrivals == 0:
            return 0.0
        return self.total_rejections / self.total_arrivals
    
    def get_stats(self) -> dict:
        """Retourne les statistiques du système"""
        return {
            'system_id': self.system_id,
            'total_arrivals': self.total_arrivals,
            'total_rejections': self.total_rejections,
            'jobs_completed': self.jobs_completed,
            'blocking_probability': self.get_blocking_probability()
        }


class WaterfallScenario:
    """
    Scénario Waterfall complet avec analyse des capacités
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 num_servers: int,
                 max_queue_size: int):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            num_servers: Nombre de serveurs (ks)
            max_queue_size: Taille de la file (kf)
        """
        self.env = env
        self.logger = logger
        
        # File limitée
        self.limited_queue = LimitedQueue(
            env=env,
            queue_id="waterfall_queue",
            max_queue_size=max_queue_size,
            num_servers=num_servers,
            logger=logger
        )
        
        # Loss system pour comparaison
        self.loss_system = LossSystem(
            env=env,
            system_id="loss_system",
            num_servers=num_servers,
            logger=logger
        )
    
    def run_comparison(self, 
                      arrival_rate: float,
                      service_rate: float,
                      duration: float) -> dict:
        """
        Compare les deux approches (avec/sans file)
        
        Args:
            arrival_rate: Taux d'arrivée λ
            service_rate: Taux de service μ
            duration: Durée de la simulation
            
        Returns:
            Dictionnaire avec les résultats comparatifs
        """
        import random
        
        def service_time_gen():
            return random.expovariate(service_rate)
        
        # Générateurs pour les deux systèmes
        from src.core.simulation_engine import Job
        
        def arrivals_limited_queue():
            while self.env.now < duration:
                interarrival = random.expovariate(arrival_rate)
                yield self.env.timeout(interarrival)
                
                if self.env.now >= duration:
                    break
                
                job = Job(arrival_time=self.env.now, job_type="ING")
                self.env.process(self.limited_queue.process_job(job, service_time_gen))
        
        def arrivals_loss_system():
            while self.env.now < duration:
                interarrival = random.expovariate(arrival_rate)
                yield self.env.timeout(interarrival)
                
                if self.env.now >= duration:
                    break
                
                job = Job(arrival_time=self.env.now, job_type="ING")
                self.env.process(self.loss_system.process_job(job, service_time_gen))
        
        # Lancement des processus
        self.env.process(arrivals_limited_queue())
        self.env.process(arrivals_loss_system())
        
        # Exécution
        self.env.run(until=duration)
        
        # Résultats
        return {
            'limited_queue': self.limited_queue.get_stats(),
            'loss_system': self.loss_system.get_stats(),
            'comparison': {
                'queue_advantage': self.limited_queue.jobs_completed - self.loss_system.jobs_completed,
                'queue_rejection_rate': self.limited_queue.get_rejection_rate(),
                'loss_blocking_probability': self.loss_system.get_blocking_probability()
            }
        }
