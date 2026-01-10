"""
Module Capacity - Gestion des Capacités et Files Finies
Étudiant 2: Gestion des Capacités (Scénario Waterfall)
"""

from __future__ import annotations
from typing import Optional, Callable, Generator

import simpy
import random

from src.core.simulation_engine import EventType, Job, SimulationLogger


class LimitedQueue:
    """
    File d'attente avec capacité limitée
    """

    def __init__(
        self,
        env: simpy.Environment,
        queue_id: str,
        max_queue_size: Optional[int],
        num_servers: int,
        logger: SimulationLogger,
        time_generator: Callable[[], float],
        on_done: Optional[Callable[[Job], Generator]] = None,
    ):
        """
        Args:
            env: Environnement SimPy
            queue_id: Identifiant de la file
            max_queue_size: Taille maximale de la file d'attente
            num_servers: Nombre de serveurs
            logger: Logger centralisé
        """
        self.env = env
        self.queue_id = queue_id
        self.max_queue_size = max_queue_size
        self.num_servers = num_servers
        self.logger = logger
        self.time_generator = time_generator
        self.on_done = on_done

        # Resource SimPy avec capacité limitée
        # Capacité totale = serveurs + file d'attente
        self.resource = simpy.Resource(env, capacity=num_servers)

        # Statistiques
        self.total_arrivals = 0
        self.total_rejections = 0
        self.rejections_queue_full = 0  # File pleine
        self.jobs_completed = 0

    @property
    def queue_length(self) -> int:
        """Retourne la longueur actuelle de la file"""
        return len(self.resource.queue)

    @property
    def total_in_system(self) -> int:
        """Retourne le nombre total d'entités dans le système"""
        return self.resource.count + len(self.resource.queue)

    @property
    def is_queue_full(self) -> bool:
        """Vérifie si la file d'attente est pleine"""
        return (
            self.max_queue_size is not None
            and len(self.resource.queue) >= self.max_queue_size
        )

    @property
    def is_server_full(self) -> bool:
        """Vérifie si tous les serveurs sont occupés"""
        return self.resource.count >= self.num_servers

    @property
    def rejection_rate(self) -> float:
        """Calcule le taux de rejet"""
        if self.total_arrivals == 0:
            return 0.0
        return self.total_rejections / self.total_arrivals

    def get_stats(self) -> dict:
        """Retourne les statistiques de la file"""
        return {
            "queue_id": self.queue_id,
            "total_arrivals": self.total_arrivals,
            "total_rejections": self.total_rejections,
            "rejections_queue_full": self.rejections_queue_full,
            "jobs_completed": self.jobs_completed,
            "rejection_rate": self.rejection_rate,
            "completion_rate": (
                self.jobs_completed / self.total_arrivals
                if self.total_arrivals > 0
                else 0.0
            ),
        }

    def process_job(self, job: Job):
        """
        Traite un job avec gestion des capacités limitées

        Args:
            job: Le job à traiter
            service_time_generator: Fonction générant le temps de service
        """
        self.total_arrivals += 1

        total_in_system = self.total_in_system

        if self.max_queue_size is not None and total_in_system >= (
            self.num_servers + self.max_queue_size
        ):
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
                queue_length=self.queue_length,
                extra_data={
                    "rejection_reason": "queue_full",
                    "total_in_system": total_in_system,
                },
            )
            return

        with self.resource.request() as request:
            yield request

            job.start_time = self.env.now
            job.server_id = self.queue_id
            service_time = self.time_generator()
            job.service_time = service_time

            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.queue_id,
                queue_length=self.queue_length,
            )

            yield self.env.timeout(service_time)

            job.end_time = self.env.now
            self.jobs_completed += 1

            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=self.queue_id,
                queue_length=self.queue_length,
                extra_data={
                    "service_time": service_time,
                    "waiting_time": job.get_waiting_time(),
                    "response_time": job.get_response_time(),
                },
            )

        if self.on_done is not None:
            yield from self.on_done(job)


class WaterfallScenario:
    """
    Scénario Waterfall complet avec analyse des capacités
    """

    def __init__(
        self,
        env: simpy.Environment,
        logger: SimulationLogger,
        num_servers: int,
        execution_queue_size: Optional[int],
        execution_rate: float,
        feedback_queue_size: Optional[int],
        feedback_rate: float,
        arrival_rate: float,
        duration: float,
        finite: bool = True,
    ):
        """
        Args:
            env: Environnement SimPy
            logger: Logger centralisé
            num_servers: Nombre de serveurs
            execution_queue_size: Size of the execution queue
            execution_rate: Processing rate for a execution job
            feedback_queue_size: Size of the execution queue
            feedback_rate: Processing rate for a feedback job
            arrival_rate: Arrival rate of submissions
            duration: Duration of the simulation
        """
        self.env = env
        self.logger = logger
        self.duration = duration
        self.finite = finite
        self.completed_jobs = []
        self.execution_time_generator = lambda: random.expovariate(execution_rate)
        self.feedback_time_generator = lambda: random.expovariate(feedback_rate)
        self.arrival_time_generator = lambda: random.expovariate(arrival_rate)

        exec_size = execution_queue_size if finite else None
        feed_size = feedback_queue_size if finite else None

        def _on_feedback_done(job):
            self.completed_jobs.append(job)
            yield self.env.timeout(0)

        self.feedback_queue = LimitedQueue(
            env=env,
            queue_id=f"feedback_queue_{feed_size or 'infinite'}",
            max_queue_size=feed_size,
            num_servers=1,
            logger=logger,
            time_generator=self.feedback_time_generator,
            on_done=_on_feedback_done,
        )
        self.execution_queue = LimitedQueue(
            env=env,
            queue_id=f"execution_queue_{exec_size or 'infinite'}",
            max_queue_size=exec_size,
            num_servers=num_servers,
            logger=logger,
            time_generator=self.execution_time_generator,
            on_done=self.feedback_queue.process_job,
        )

    def arrivals(self):
        while self.env.now < self.duration:
            yield self.env.timeout(self.arrival_time_generator())

            if self.env.now >= self.duration:
                break

            job = Job(arrival_time=self.env.now, job_type="ING")
            self.env.process(self.execution_queue.process_job(job))

    def compare(
        self,
        scenario: WaterfallScenario,
    ) -> dict:
        """
        Compare les deux approches

        Args:
            scenario: Scenario to compare against

        Returns:
            Dictionnaire avec les résultats comparatifs
        """

        # Résultats
        return {
            f"{self.execution_queue.queue_id}": self.execution_queue.get_stats(),
            f"{scenario.execution_queue.queue_id}": scenario.execution_queue.get_stats(),
            "comparison": {
                "queue_advantage": abs(
                    self.execution_queue.jobs_completed
                    - scenario.execution_queue.jobs_completed
                ),
                f"{self.execution_queue.queue_id}_rejection_rate": self.execution_queue.rejection_rate,
                f"{scenario.execution_queue.queue_id}_rejection_rate": scenario.execution_queue.rejection_rate,
            },
        }

    def get_sojourn_stats(self):
        """Calcule les statistiques de séjour (sojourn time)"""
        if not self.completed_jobs:
            return {"mean_sojourn_time": 0.0, "sojourn_variance": 0.0}

        sojourn_times = [job.end_time - job.arrival_time for job in self.completed_jobs]
        mean = sum(sojourn_times) / len(sojourn_times)
        variance = sum((t - mean) ** 2 for t in sojourn_times) / len(sojourn_times)

        return {
            "mean_sojourn_time": mean,
            "sojourn_variance": variance,
            "completed_jobs": len(self.completed_jobs),
        }
