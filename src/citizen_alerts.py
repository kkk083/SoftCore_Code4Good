import json
from datetime import datetime
from pathlib import Path
import pandas as pd


ALERTS_FILE = 'data/alerts.json'


def initialize_alerts_file():
    """Crée le fichier alerts.json s'il n'existe pas"""
    Path('data').mkdir(exist_ok=True)
    if not Path(ALERTS_FILE).exists():
        with open(ALERTS_FILE, 'w') as f:
            json.dump([], f)


def load_alerts():
    """Charge les alertes citoyennes"""
    initialize_alerts_file()
    try:
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_alert(region_id, alert_type):
    """
    Enregistre une alerte citoyenne
    
    """
    alerts = load_alerts()
    
    new_alert = {
        'id': f"{region_id}_{datetime.now().timestamp()}",
        'region_id': region_id,
        'type': alert_type,
        'timestamp': datetime.now().isoformat()
    }
    
    alerts.append(new_alert)
    
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
        return True
    except:
        return False


def get_region_alert_stats(region_id):
    """
    Calcule statistiques alertes pour une région
    
    """
    alerts = load_alerts()
    region_alerts = [a for a in alerts if a['region_id'] == region_id]
    
    danger = len([a for a in region_alerts if a['type'] == 'danger'])
    safe = len([a for a in region_alerts if a['type'] == 'safe'])
    total = len(region_alerts)
    
    return {
        'danger_count': danger,
        'safe_count': safe,
        'total_count': total,
        'danger_ratio': danger / total if total > 0 else 0
    }


def get_all_alerts_summary(df):
    """
    Résumé global des alertes pour toutes les régions

    """
    alerts_data = []
    
    for region_id in df['region_id'].unique():
        stats = get_region_alert_stats(region_id)
        alerts_data.append({
            'region_id': region_id,
            'citizen_danger': stats['danger_count'],
            'citizen_safe': stats['safe_count'],
            'citizen_total': stats['total_count'],
            'citizen_danger_ratio': stats['danger_ratio']
        })
    
    alerts_df = pd.DataFrame(alerts_data)
    return df.merge(alerts_df, on='region_id', how='left').fillna(0)


def clear_old_alerts(hours=24):
    """Nettoie les alertes de plus de X heures"""
    alerts = load_alerts()
    cutoff = datetime.now().timestamp() - (hours * 3600)
    
    filtered = [
        a for a in alerts 
        if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff
    ]
    
    with open(ALERTS_FILE, 'w') as f:
        json.dump(filtered, f, indent=2)
    
    return len(alerts) - len(filtered)