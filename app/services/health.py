from datetime import datetime, timedelta

class GoogleFitServices:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_dashboard_data(self, days: int):
        """Zwraca dane mockowane - w rzeczywistości połączenie z API"""
        return {
            "daily_stats": self._get_daily_stats(days),
            "charts": self._get_charts_data(days)
        }

    def _get_daily_stats(self, days):
        return {
            "steps": 8450,
            "goal_steps": 10000,
            "avg_heart_rate": 72,
            "resting_heart_rate": 65,
            "max_heart_rate": 130,
            "sleep_hours": 7.5,
            "goal_sleep_hours": 8,
            "distance": 5.2,
            "weight": 70.5,
            "bmi": 23.1,
            "weight_change": -0.3
        }

    def _get_charts_data(self, days):
        labels = [f"Dzień {i}" for i in range(1, days+1)]
        return {
            "activity": {
                "labels": labels,
                "steps": [8200, 7500, 9100, 10200, 7300, 8600, 8450][:days],
                "distance": [5.7, 5.2, 6.4, 7.1, 5.1, 6.0, 5.2][:days]
            },
            "heart_rate": {
                "labels": labels,
                "avg": [72, 71, 73, 74, 70, 69, 72][:days],
                "max": [125, 130, 135, 128, 122, 118, 130][:days]
            }
        }