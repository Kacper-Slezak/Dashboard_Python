def _parse_sleep(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
    sleep_data = []
    sleep_stages = {1: "awake", 2: "light", 3: "deep", 4: "rem"}
    
    for bucket in response.get("bucket", []):
        date_millis = int(bucket.get("startTimeMillis", 0))
        date = datetime.fromtimestamp(date_millis / 1000)
        
        sleep_segments = []
        
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                start_time_nanos = point.get("startTimeNanos", 0)
                end_time_nanos = point.get("endTimeNanos", 0)
                
                start_time = datetime.fromtimestamp(start_time_nanos / 1e9)
                end_time = datetime.fromtimestamp(end_time_nanos / 1e9)
                
                duration = (end_time - start_time).total_seconds() / 60
                for value in point.get("value", []):
                    if "intVal" in value:
                        stage = sleep_stages.get(value.get("intVal"), "unknown")
                        sleep_segments.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": duration,
                            "stage": stage
                        })
        if sleep_segments:
            total_minutes = sum(segment["duration"] for segment in sleep_segments)
            light_minutes = sum(s["duration"] for s in sleep_segments if s["stage"] == "light")
            deep_minutes = sum(s["duration"] for s in sleep_segments if s["stage"] == "deep")
            rem_minutes = sum(s["duration"] for s in sleep_segments if s["stage"] == "rem")
            awake_minutes = sum(s["duration"] for s in sleep_segments if s["stage"] == "awake")
            
            sleep_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_minutes": total_minutes,
                "light_minutes": light_minutes,
                "deep_minutes": deep_minutes,
                "rem_minutes": rem_minutes,
                "awake_minutes": awake_minutes,
                "efficiency": (total_minutes - awake_minutes) / total_minutes * 100 if total_minutes > 0 else 0
            })
    # Przesunięty return poza pętlę for
    return sleep_data