"""
Tests unitaires pour le module Capacity
"""

import pytest
import random
from unittest.mock import MagicMock

from src.core import SimulationEngine, Job
from src.capacity import LimitedQueue, WaterfallScenario


@pytest.fixture
def simulation_engine():
    """Fixture pour le moteur de simulation"""
    return SimulationEngine(random_seed=42)


@pytest.fixture
def mock_logger():
    """Fixture pour le logger mocké"""
    return MagicMock()


def test_limited_queue_no_rejection_when_capacity_available(
    simulation_engine, mock_logger
):
    """Test des propriétés de LimitedQueue"""

    def time_gen():
        return 1.0

    queue = LimitedQueue(
        env=simulation_engine.env,
        queue_id="test_queue",
        max_queue_size=2,
        num_servers=1,
        logger=mock_logger,
        time_generator=time_gen,
    )

    # Initially empty
    assert queue.queue_length == 0
    assert queue.total_in_system == 0
    assert not queue.is_queue_full
    assert not queue.is_server_full

    # Add a job to server
    job = Job(arrival_time=0, job_type="ING")
    simulation_engine.env.process(queue.process_job(job))
    simulation_engine.run(0.1)  # Partial run

    # Check properties
    assert queue.total_in_system >= 1
    assert queue.is_server_full or queue.queue_length > 0


def test_limited_queue_rejection_when_full(simulation_engine, mock_logger):
    """Test de rejet quand la file est pleine"""

    def time_gen():
        return 10.0  # Long service time

    queue = LimitedQueue(
        env=simulation_engine.env,
        queue_id="test_queue",
        max_queue_size=1,  # Small queue
        num_servers=1,
        logger=mock_logger,
        time_generator=time_gen,
    )

    # Fill the queue
    jobs = []
    for i in range(3):  # More than capacity
        job = Job(arrival_time=simulation_engine.env.now, job_type="ING")
        jobs.append(job)
        simulation_engine.env.process(queue.process_job(job))

    simulation_engine.run(1.0)  # Run briefly

    stats = queue.get_stats()
    assert stats["total_arrivals"] == 3
    assert stats["total_rejections"] > 0
    assert stats["rejection_rate"] > 0

    def time_gen():
        return 0.1  # Fast service

    queue = LimitedQueue(
        env=simulation_engine.env,
        queue_id="test_queue",
        max_queue_size=10,
        num_servers=2,
        logger=mock_logger,
        time_generator=time_gen,
    )

    # Add some jobs
    for i in range(5):
        job = Job(arrival_time=simulation_engine.env.now, job_type="ING")
        simulation_engine.env.process(queue.process_job(job))

    simulation_engine.run(2.0)

    stats = queue.get_stats()
    assert stats["total_arrivals"] == 5
    assert 0 <= stats["rejection_rate"] <= 1
    assert 0 <= stats["completion_rate"] <= 1


@pytest.mark.parametrize(
    "max_queue_size,num_servers,expected_capacity",
    [
        (5, 2, 7),  # 2 servers + 5 queue
        (0, 1, 1),  # 1 server + 0 queue
        (10, 3, 13),
    ],
)
def test_limited_queue_capacity_calculation(
    simulation_engine, mock_logger, max_queue_size, num_servers, expected_capacity
):
    """Test du calcul de capacité totale"""

    def time_gen():
        return 1.0

    queue = LimitedQueue(
        env=simulation_engine.env,
        queue_id="test_queue",
        max_queue_size=max_queue_size,
        num_servers=num_servers,
        logger=mock_logger,
        time_generator=time_gen,
    )

    # Check that rejections happen when exceeding total capacity
    jobs = []
    for i in range(expected_capacity + 2):
        job = Job(arrival_time=simulation_engine.env.now, job_type="ING")
        jobs.append(job)
        simulation_engine.env.process(queue.process_job(job))

    simulation_engine.run(0.1)

    stats = queue.get_stats()
    assert stats["total_rejections"] >= 2  # At least the extra ones rejected


def test_waterfall_scenario_job_flow(simulation_engine, mock_logger):
    """Test du flux de jobs dans WaterfallScenario"""
    scenario = WaterfallScenario(
        env=simulation_engine.env,
        logger=mock_logger,
        num_servers=1,
        execution_queue_size=2,
        execution_rate=10.0,  # Fast execution
        feedback_queue_size=2,
        feedback_rate=10.0,  # Fast feedback
        arrival_rate=1.0,  # Slow arrivals
        duration=20.0,
    )

    simulation_engine.env.process(scenario.arrivals())
    simulation_engine.run(scenario.duration)

    # Check that jobs went through execution queue
    exec_stats = scenario.execution_queue.get_stats()
    feedback_stats = scenario.feedback_queue.get_stats()

    assert exec_stats["total_arrivals"] > 0
    assert exec_stats["jobs_completed"] > 0
    # Feedback should have received jobs from execution completion
    assert feedback_stats["total_arrivals"] >= exec_stats["jobs_completed"]


def test_waterfall_scenario_infinite_queues():
    """Test des files infinies dans Waterfall"""
    engine = SimulationEngine(random_seed=42)
    logger = MagicMock()
    scenario = WaterfallScenario(
        env=engine.env,
        logger=logger,
        num_servers=2,
        execution_queue_size=5,  # Will be ignored since finite=False
        execution_rate=2.0,
        feedback_queue_size=3,
        feedback_rate=1.0,
        arrival_rate=3.0,
        duration=10.0,
        finite=False,  # Infinite queues
    )

    engine.env.process(scenario.arrivals())
    engine.run(scenario.duration)

    # With infinite queues, no rejections
    exec_stats = scenario.execution_queue.get_stats()
    feed_stats = scenario.feedback_queue.get_stats()
    sojourn_stats = scenario.get_sojourn_stats()

    assert exec_stats["total_rejections"] == 0
    assert feed_stats["total_rejections"] == 0
    assert sojourn_stats["completed_jobs"] > 0
    assert sojourn_stats["mean_sojourn_time"] > 0
    assert sojourn_stats["sojourn_variance"] >= 0


def test_waterfall_scenario_no_jobs_when_no_arrivals():
    """Test qu'aucun job n'arrive si durée nulle"""
    engine = SimulationEngine(random_seed=42)
    logger = MagicMock()
    scenario = WaterfallScenario(
        env=engine.env,
        logger=logger,
        num_servers=1,
        execution_queue_size=5,
        execution_rate=2.0,
        feedback_queue_size=3,
        feedback_rate=1.0,
        arrival_rate=1.0,
        duration=0.0,  # No time for arrivals
    )

    engine.env.process(scenario.arrivals())
    engine.run(1.0)

    stats = scenario.execution_queue.get_stats()
    assert stats["total_arrivals"] == 0
