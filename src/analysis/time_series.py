"""
Module Time Series - Analyse Temporelle et Rejeu de Données Réelles

Ce module implémente:
- Rejeu exact des timestamps réels
- Analyse de patterns temporels
- Détection de pics de charge
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import simpy
from ..core import Job, SimulationLogger


class TimeSeriesAnalyzer:
    """
    Analyseur de séries temporelles pour données réelles
    """
    
    def __init__(self, real_data: pd.DataFrame):
        """
        Args:
            real_data: DataFrame avec colonne 'receivedAt' (timestamps)
        """
        self.real_data = real_data.copy()
        
        # Assurer que receivedAt est en datetime
        if not pd.api.types.is_datetime64_any_dtype(self.real_data['receivedAt']):
            self.real_data['receivedAt'] = pd.to_datetime(self.real_data['receivedAt'])
        
        self.real_data = self.real_data.sort_values('receivedAt')
    
    def analyze_temporal_patterns(self) -> Dict:
        """
        Analyse les patterns temporels dans les données réelles
        
        Returns:
            Dictionnaire avec l'analyse des patterns
        """
        df = self.real_data.copy()
        
        # Extraction des composantes temporelles
        df['hour'] = df['receivedAt'].dt.hour
        df['day_of_week'] = df['receivedAt'].dt.dayofweek
        df['date'] = df['receivedAt'].dt.date
        
        # Analyse par heure de la journée
        hourly_counts = df.groupby('hour').size()
        peak_hour = hourly_counts.idxmax()
        min_hour = hourly_counts.idxmin()
        
        # Analyse par jour de la semaine
        daily_counts = df.groupby('day_of_week').size()
        peak_day = daily_counts.idxmax()
        
        # Calcul des taux d'arrivée variables
        df['interarrival'] = df['receivedAt'].diff().dt.total_seconds()
        hourly_rates = {}
        
        for hour in range(24):
            hour_data = df[df['hour'] == hour]['interarrival'].dropna()
            if len(hour_data) > 0:
                mean_interarrival = hour_data.mean()
                hourly_rates[hour] = 1.0 / mean_interarrival if mean_interarrival > 0 else 0
            else:
                hourly_rates[hour] = 0
        
        # Détection de pics
        daily_aggregates = df.groupby('date').size()
        mean_daily = daily_aggregates.mean()
        std_daily = daily_aggregates.std()
        peak_days = daily_aggregates[daily_aggregates > mean_daily + 2 * std_daily]
        
        days_of_week = {0: 'Lundi', 1: 'Mardi', 2: 'Mercredi', 3: 'Jeudi', 
                       4: 'Vendredi', 5: 'Samedi', 6: 'Dimanche'}
        
        return {
            'total_submissions': len(df),
            'period': {
                'start': df['receivedAt'].min(),
                'end': df['receivedAt'].max(),
                'duration_days': (df['receivedAt'].max() - df['receivedAt'].min()).days
            },
            'hourly_pattern': {
                'peak_hour': int(peak_hour),
                'min_hour': int(min_hour),
                'peak_rate': hourly_rates[peak_hour],
                'min_rate': hourly_rates[min_hour],
                'ratio_peak_to_min': hourly_rates[peak_hour] / hourly_rates[min_hour] if hourly_rates[min_hour] > 0 else float('inf'),
                'all_hourly_rates': hourly_rates
            },
            'weekly_pattern': {
                'peak_day': days_of_week[peak_day],
                'peak_day_count': int(daily_counts[peak_day]),
                'counts_by_day': {days_of_week[day]: int(count) for day, count in daily_counts.items()}
            },
            'peak_detection': {
                'mean_daily_submissions': mean_daily,
                'std_daily_submissions': std_daily,
                'peak_days_count': len(peak_days),
                'peak_days': peak_days.to_dict() if len(peak_days) > 0 else {}
            }
        }
    
    def get_time_varying_lambda(self, time_of_day: float) -> float:
        """
        Retourne le taux d'arrivée λ(t) pour une heure donnée
        
        Args:
            time_of_day: Heure du jour (0-24)
            
        Returns:
            Taux d'arrivée pour cette heure
        """
        patterns = self.analyze_temporal_patterns()
        hourly_rates = patterns['hourly_pattern']['all_hourly_rates']
        
        hour = int(time_of_day) % 24
        return hourly_rates.get(hour, 0)
    
    def extract_interarrival_times(self, max_duration: Optional[float] = None) -> List[float]:
        """
        Extrait les temps inter-arrivées réels
        
        Args:
            max_duration: Durée maximale à extraire (en secondes)
            
        Returns:
            Liste des temps inter-arrivées
        """
        df = self.real_data.copy()
        df['interarrival'] = df['receivedAt'].diff().dt.total_seconds()
        
        interarrivals = df['interarrival'].dropna().tolist()
        
        if max_duration:
            cumulative = 0
            filtered = []
            for ia in interarrivals:
                if cumulative + ia > max_duration:
                    break
                filtered.append(ia)
                cumulative += ia
            return filtered
        
        return interarrivals
    
    def create_time_series_report(self, output_file: str = 'time_series_analysis.txt'):
        """
        Génère un rapport d'analyse temporelle
        
        Args:
            output_file: Fichier de sortie
        """
        patterns = self.analyze_temporal_patterns()
        
        report = []
        report.append("=" * 80)
        report.append("ANALYSE TEMPORELLE DES DONNÉES RÉELLES")
        report.append("=" * 80)
        report.append("")
        
        report.append(f"Période analysée:")
        report.append(f"  Début: {patterns['period']['start']}")
        report.append(f"  Fin: {patterns['period']['end']}")
        report.append(f"  Durée: {patterns['period']['duration_days']} jours")
        report.append(f"  Total soumissions: {patterns['total_submissions']}")
        report.append("")
        
        report.append("Patterns horaires:")
        report.append(f"  Heure de pic: {patterns['hourly_pattern']['peak_hour']}h")
        report.append(f"  Taux au pic: {patterns['hourly_pattern']['peak_rate']:.6f} jobs/s")
        report.append(f"  Heure creuse: {patterns['hourly_pattern']['min_hour']}h")
        report.append(f"  Taux au creux: {patterns['hourly_pattern']['min_rate']:.6f} jobs/s")
        report.append(f"  Ratio pic/creux: {patterns['hourly_pattern']['ratio_peak_to_min']:.2f}x")
        report.append("")
        
        report.append("Patterns hebdomadaires:")
        report.append(f"  Jour de pic: {patterns['weekly_pattern']['peak_day']}")
        report.append(f"  Soumissions au pic: {patterns['weekly_pattern']['peak_day_count']}")
        report.append("")
        report.append("  Distribution par jour:")
        for day, count in patterns['weekly_pattern']['counts_by_day'].items():
            report.append(f"    {day}: {count}")
        report.append("")
        
        report.append("Détection de pics:")
        report.append(f"  Moyenne quotidienne: {patterns['peak_detection']['mean_daily_submissions']:.1f}")
        report.append(f"  Écart-type: {patterns['peak_detection']['std_daily_submissions']:.1f}")
        report.append(f"  Jours de pic détectés: {patterns['peak_detection']['peak_days_count']}")
        report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        print(f"Rapport sauvegardé dans {output_file}")
        return report_text


class ReplaySimulation:
    """
    Rejeu exact des timestamps réels
    """
    
    def __init__(self, 
                 real_timestamps: List[datetime],
                 env: simpy.Environment,
                 logger: SimulationLogger):
        """
        Args:
            real_timestamps: Liste des timestamps réels
            env: Environnement SimPy
            logger: Logger centralisé
        """
        self.real_timestamps = sorted(real_timestamps)
        self.env = env
        self.logger = logger
    
    def replay_arrivals(self, 
                       server,
                       service_time_generator,
                       duration: Optional[float] = None,
                       time_scale: float = 1.0):
        """
        Rejeu des arrivées selon les timestamps réels
        
        Args:
            server: Serveur qui traitera les jobs
            service_time_generator: Générateur de temps de service
            duration: Durée maximale de simulation (None = tous les timestamps)
            time_scale: Facteur d'échelle temporelle (1.0 = temps réel)
        """
        # Convertir timestamps en temps relatifs (secondes depuis le premier)
        if not self.real_timestamps:
            return
        
        start_time = self.real_timestamps[0]
        
        from src.core import EventType
        
        for i, timestamp in enumerate(self.real_timestamps):
            # Calcul du temps relatif
            relative_time = (timestamp - start_time).total_seconds() * time_scale
            
            if duration and relative_time > duration:
                break
            
            # Attendre jusqu'à ce timestamp
            wait_time = relative_time - self.env.now
            if wait_time > 0:
                yield self.env.timeout(wait_time)
            
            # Créer et traiter le job
            job = Job(
                arrival_time=self.env.now,
                job_type="ING",
                assignment=f"real_submission_{i}"
            )
            
            # Log arrival event
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.ARRIVAL,
                entity_id=job.id,
                entity_type=job.job_type,
                server_id=server.server_id,
                queue_length=len(server.resource.queue)
            )
            
            self.env.process(server.process(job, service_time_generator))
    
    def replay_with_time_varying_service(self,
                                        server,
                                        service_time_func,
                                        duration: Optional[float] = None):
        """
        Rejeu avec temps de service variable selon l'heure
        
        Args:
            server: Serveur
            service_time_func: Fonction (hour_of_day) -> service_time
            duration: Durée maximale
        """
        if not self.real_timestamps:
            return
        
        start_time = self.real_timestamps[0]
        
        for i, timestamp in enumerate(self.real_timestamps):
            relative_time = (timestamp - start_time).total_seconds()
            
            if duration and relative_time > duration:
                break
            
            wait_time = relative_time - self.env.now
            if wait_time > 0:
                yield self.env.timeout(wait_time)
            
            # Temps de service dépend de l'heure
            hour_of_day = timestamp.hour
            
            def service_gen():
                return service_time_func(hour_of_day)
            
            job = Job(
                arrival_time=self.env.now,
                job_type="ING",
                assignment=f"real_{i}"
            )
            
            self.env.process(server.process(job, service_gen))
