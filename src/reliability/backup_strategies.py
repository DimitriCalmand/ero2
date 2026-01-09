"""
Module Reliability - Fiabilité et Stratégies de Backup
Étudiant 3: Fiabilité & Stratégies de Backup

Ce module implémente:
- Délais de sauvegarde avant traitement
- Backup Systématique vs Backup Aléatoire
- Analyse d'impact sur le débit et la congestion
"""

import simpy
import random
from typing import Optional, Callable
from src.core.simulation_engine import SimulationLogger, EventType, Job


class BackupStrategy:
    """Stratégie de base pour les backups"""
    
    def should_backup(self, job: Job) -> bool:
        """
        Détermine si un job doit être sauvegardé
        
        Args:
            job: Le job à évaluer
            
        Returns:
            True si le job doit être sauvegardé
        """
        raise NotImplementedError


class SystematicBackup(BackupStrategy):
    """
    Backup systématique: tous les jobs sont sauvegardés
    Risque de congestion synchronisée
    """
    
    def should_backup(self, job: Job) -> bool:
        return True
    
    def __repr__(self):
        return "SystematicBackup"


class RandomBackup(BackupStrategy):
    """
    Backup aléatoire: seulement une fraction des jobs est sauvegardée
    Réduit le risque de congestion
    """
    
    def __init__(self, backup_probability: float = 0.5):
        """
        Args:
            backup_probability: Probabilité de sauvegarder un job (0 à 1)
        """
        self.backup_probability = backup_probability
    
    def should_backup(self, job: Job) -> bool:
        return random.random() < self.backup_probability
    
    def __repr__(self):
        return f"RandomBackup(p={self.backup_probability})"


class ConditionalBackup(BackupStrategy):
    """
    Backup conditionnel: basé sur la charge du système
    """
    
    def __init__(self, 
                 threshold: int,
                 get_queue_length: Callable[[], int]):
        """
        Args:
            threshold: Seuil de longueur de file
            get_queue_length: Fonction retournant la longueur actuelle de la file
        """
        self.threshold = threshold
        self.get_queue_length = get_queue_length
    
    def should_backup(self, job: Job) -> bool:
        # Sauvegarder seulement si la file est courte
        return self.get_queue_length() < self.threshold
    
    def __repr__(self):
        return f"ConditionalBackup(threshold={self.threshold})"


class ReliableServer:
    """
    Serveur avec stratégie de backup
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 server_id: str,
                 num_servers: int,
                 logger: SimulationLogger,
                 backup_strategy: BackupStrategy,
                 backup_time_generator: Callable[[], float]):
        """
        Args:
            env: Environnement SimPy
            server_id: Identifiant du serveur
            num_servers: Nombre de serveurs en parallèle
            logger: Logger centralisé
            backup_strategy: Stratégie de backup à utiliser
            backup_time_generator: Fonction générant les temps de backup
        """
        self.env = env
        self.server_id = server_id
        self.resource = simpy.Resource(env, capacity=num_servers)
        self.logger = logger
        self.backup_strategy = backup_strategy
        self.backup_time_generator = backup_time_generator
        
        # Statistiques
        self.jobs_processed = 0
        self.jobs_backed_up = 0
        self.total_backup_time = 0.0
        self.total_service_time = 0.0
    
    def process_with_backup(self, job: Job, service_time_generator: Callable[[], float]):
        """
        Traite un job avec sauvegarde optionnelle
        
        Args:
            job: Le job à traiter
            service_time_generator: Fonction générant le temps de service
        """
        with self.resource.request() as request:
            yield request
            
            job.start_time = self.env.now
            job.server_id = self.server_id
            
            # Décision de backup
            needs_backup = self.backup_strategy.should_backup(job)
            backup_time = 0.0
            
            if needs_backup:
                # Phase de backup
                backup_time = self.backup_time_generator()
                
                self.logger.log_event(
                    time=self.env.now,
                    event_type=EventType.BACKUP_START,
                    entity_id=job.id,
                    entity_type=job.job_type,
                    server_id=self.server_id,
                    queue_length=len(self.resource.queue),
                    extra_data={'backup_time': backup_time}
                )
                
                yield self.env.timeout(backup_time)
                
                self.jobs_backed_up += 1
                self.total_backup_time += backup_time
                
                self.logger.log_event(
                    time=self.env.now,
                    event_type=EventType.BACKUP_END,
                    entity_id=job.id,
                    entity_type=job.job_type,
                    server_id=self.server_id,
                    queue_length=len(self.resource.queue)
                )
            
            # Phase de service normale
            service_time = service_time_generator()
            job.service_time = service_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.server_id,
                queue_length=len(self.resource.queue),
                extra_data={
                    'backup_done': needs_backup,
                    'backup_time': backup_time
                }
            )
            
            yield self.env.timeout(service_time)
            
            # Fin du traitement
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
                    'backup_time': backup_time,
                    'total_processing_time': service_time + backup_time,
                    'waiting_time': job.get_waiting_time(),
                    'response_time': job.get_response_time()
                }
            )
    
    def get_stats(self) -> dict:
        """Retourne les statistiques du serveur"""
        avg_backup_time = (self.total_backup_time / self.jobs_backed_up 
                          if self.jobs_backed_up > 0 else 0.0)
        
        return {
            'server_id': self.server_id,
            'jobs_processed': self.jobs_processed,
            'jobs_backed_up': self.jobs_backed_up,
            'backup_rate': self.jobs_backed_up / self.jobs_processed if self.jobs_processed > 0 else 0.0,
            'total_backup_time': self.total_backup_time,
            'total_service_time': self.total_service_time,
            'avg_backup_time': avg_backup_time,
            'backup_strategy': str(self.backup_strategy)
        }


class BackupComparison:
    """
    Comparaison de différentes stratégies de backup
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
        """
        self.env = env
        self.logger = logger
        self.servers = {}
    
    def add_server(self,
                   server_id: str,
                   num_servers: int,
                   backup_strategy: BackupStrategy,
                   backup_time_generator: Callable[[], float]):
        """
        Ajoute un serveur avec une stratégie de backup
        
        Args:
            server_id: Identifiant unique
            num_servers: Nombre de serveurs en parallèle
            backup_strategy: Stratégie de backup
            backup_time_generator: Générateur de temps de backup
        """
        server = ReliableServer(
            env=self.env,
            server_id=server_id,
            num_servers=num_servers,
            logger=self.logger,
            backup_strategy=backup_strategy,
            backup_time_generator=backup_time_generator
        )
        self.servers[server_id] = server
    
    def run_comparison(self,
                      arrival_rate: float,
                      service_rate: float,
                      duration: float) -> dict:
        """
        Exécute une comparaison entre les stratégies
        
        Args:
            arrival_rate: Taux d'arrivée λ
            service_rate: Taux de service μ
            duration: Durée de la simulation
            
        Returns:
            Dictionnaire avec les résultats pour chaque stratégie
        """
        def service_time_gen():
            return random.expovariate(service_rate)
        
        # Générateur d'arrivées pour chaque serveur
        def arrivals_for_server(server_id: str):
            server = self.servers[server_id]
            
            while self.env.now < duration:
                interarrival = random.expovariate(arrival_rate)
                yield self.env.timeout(interarrival)
                
                if self.env.now >= duration:
                    break
                
                job = Job(arrival_time=self.env.now, job_type="ING")
                
                self.logger.log_event(
                    time=self.env.now,
                    event_type=EventType.ARRIVAL,
                    entity_id=job.id,
                    entity_type=job.job_type,
                    server_id=server_id,
                    queue_length=len(server.resource.queue)
                )
                
                self.env.process(server.process_with_backup(job, service_time_gen))
        
        # Lancer un processus d'arrivées pour chaque serveur
        for server_id in self.servers:
            self.env.process(arrivals_for_server(server_id))
        
        # Exécution
        self.env.run(until=duration)
        
        # Collecte des résultats
        results = {}
        for server_id, server in self.servers.items():
            results[server_id] = server.get_stats()
        
        return results


class FailureRecovery:
    """
    Gestion des pannes et récupération
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 failure_rate: float,
                 recovery_time_generator: Callable[[], float]):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            failure_rate: Taux de pannes (λ_failure)
            recovery_time_generator: Générateur de temps de récupération
        """
        self.env = env
        self.logger = logger
        self.failure_rate = failure_rate
        self.recovery_time_generator = recovery_time_generator
        
        self.is_operational = True
        self.total_downtime = 0.0
        self.failure_count = 0
    
    def failure_process(self):
        """
        Processus simulant les pannes aléatoires
        """
        while True:
            # Attente jusqu'à la prochaine panne
            time_to_failure = random.expovariate(self.failure_rate)
            yield self.env.timeout(time_to_failure)
            
            # Panne
            self.is_operational = False
            self.failure_count += 1
            failure_start = self.env.now
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.REJECTION,  # Utilisation pour indiquer une panne
                entity_id=-1,
                entity_type="SYSTEM",
                server_id="failure_recovery",
                queue_length=0,
                extra_data={'event': 'failure', 'failure_number': self.failure_count}
            )
            
            # Temps de récupération
            recovery_time = self.recovery_time_generator()
            yield self.env.timeout(recovery_time)
            
            # Récupération
            self.is_operational = True
            self.total_downtime += recovery_time
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.ARRIVAL,  # Utilisation pour indiquer une récupération
                entity_id=-1,
                entity_type="SYSTEM",
                server_id="failure_recovery",
                queue_length=0,
                extra_data={
                    'event': 'recovery',
                    'downtime': recovery_time,
                    'total_downtime': self.total_downtime
                }
            )
    
    def get_availability(self, simulation_time: float) -> float:
        """
        Calcule la disponibilité du système
        
        Args:
            simulation_time: Temps total de simulation
            
        Returns:
            Disponibilité (uptime / total_time)
        """
        if simulation_time == 0:
            return 1.0
        return 1.0 - (self.total_downtime / simulation_time)
    
    def get_stats(self, simulation_time: float) -> dict:
        """Retourne les statistiques de fiabilité"""
        return {
            'failure_count': self.failure_count,
            'total_downtime': self.total_downtime,
            'availability': self.get_availability(simulation_time),
            'mtbf': simulation_time / self.failure_count if self.failure_count > 0 else float('inf'),
            'mttr': self.total_downtime / self.failure_count if self.failure_count > 0 else 0.0
        }
