import pandas as pd
from utils.config import RESILIENCE_WEIGHTS, RESILIENCE_THRESHOLDS


def calculate_resilience(exposure: float, vulnerability: float, adaptation: float) -> float:
    """
    Calcule l'indice de résilience pour une seule région.

    Paramètres
    ----------
    exposure : float
        Exposition (0 à 100).
    vulnerability : float
        Vulnérabilité (0 à 100).
    adaptation : float
        Capacité d'adaptation (0 à 100).

    Returns
    -------
    float
        Indice de résilience entre 0 et 100 (arrondi à 2 décimales).
    """
    composite_risk = (
        RESILIENCE_WEIGHTS["exposure"] * exposure +
        RESILIENCE_WEIGHTS["vulnerability"] * vulnerability -
        RESILIENCE_WEIGHTS["adaptation"] * adaptation
    )

    resilience_index = 100 - composite_risk

    # On force entre 0 et 100
    resilience_index = max(0, min(100, resilience_index))

    return round(resilience_index, 2)


def calculate_resilience_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'indice de résilience pour chaque ligne d'un DataFrame.

    Ce DataFrame est typiquement celui qui vient de load_resilience_data()
    (Dev1) avec les colonnes :
    - exposure
    - vulnerability
    - adaptation

    Returns
    -------
    pandas.DataFrame
        Même DataFrame mais avec une colonne en plus :
        - resilience_index
    """
    required_cols = ["exposure", "vulnerability", "adaptation"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(
            "DataFrame doit contenir les colonnes: exposure, vulnerability, adaptation"
        )

    # Calcul vectorisé (plus rapide)
    composite_risk = (
        RESILIENCE_WEIGHTS["exposure"] * df["exposure"] +
        RESILIENCE_WEIGHTS["vulnerability"] * df["vulnerability"] -
        RESILIENCE_WEIGHTS["adaptation"] * df["adaptation"]
    )

    df = df.copy()
    df["resilience_index"] = 100 - composite_risk

    # Clamp entre 0 et 100 + arrondi
    df["resilience_index"] = df["resilience_index"].clip(0, 100).round(2)

    return df


def get_resilience_category(score: float) -> str:
    """
    Retourne une catégorie textuelle à partir d'un score de résilience.

    Utilise RESILIENCE_THRESHOLDS dans utils.config.
    Ex:
    - 0 <= score < 40  -> 'low'
    - 40 <= score < 70 -> 'medium'
    - 70 <= score <=100-> 'high'
    """
    for category, (min_val, max_val) in RESILIENCE_THRESHOLDS.items():
        if min_val <= score < max_val:
            return category

    if score == 100:
        return "high"

    return "low"  # fallback


def add_resilience_category_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute une colonne 'resilience_category' à un DataFrame
    qui contient déjà 'resilience_index'.
    """
    if "resilience_index" not in df.columns:
        raise ValueError("La colonne 'resilience_index' est manquante dans le DataFrame.")

    df = df.copy()
    df["resilience_category"] = df["resilience_index"].apply(get_resilience_category)
    return df


def normalize_values(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Normalise certaines colonnes sur une échelle 0-100.

    Utile si un jour vous avez des données brutes pas déjà en 0-100.
    Pour l'instant, ton CSV Dev1 utilise déjà 0-100, donc
    cette fonction est optionnelle.

    Returns
    -------
    pandas.DataFrame
        DataFrame avec les colonnes normalisées.
    """
    df_normalized = df.copy()

    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Colonne '{col}' introuvable dans le DataFrame")

        min_val = df[col].min()
        max_val = df[col].max()

        if max_val - min_val == 0:
            df_normalized[col] = 50  # neutre si tous les valeurs sont identiques
        else:
            df_normalized[col] = ((df[col] - min_val) / (max_val - min_val)) * 100

    return df_normalized


def simulate_cyclone_impact(df: pd.DataFrame, severity: int) -> pd.DataFrame:
    """
    Simule l'impact d'un cyclone en augmentant l'exposition.

    Paramètres
    ----------
    df : pandas.DataFrame
        DataFrame contenant au minimum 'exposure', 'vulnerability', 'adaptation'.
        (typiquement ton DataFrame de résilience par région)
    severity : int
        Intensité du cyclone (0 à 100). Ce sera relié au slider Streamlit.

    Returns
    -------
    pandas.DataFrame
        Nouveau DataFrame avec:
        - exposure ajustée
        - resilience_index recalculé
    """
    if not 0 <= severity <= 100:
        raise ValueError("Severity doit être entre 0 et 100")

    df_simulated = df.copy()

    # Augmente l'exposition selon la sévérité (facteur 0.5 = tuning simple)
    df_simulated["exposure"] = df_simulated["exposure"] + (severity * 0.5)
    df_simulated["exposure"] = df_simulated["exposure"].clip(0, 100)

    # Recalculer la résilience après le cyclone
    df_simulated = calculate_resilience_batch(df_simulated)

    return df_simulated


if __name__ == "__main__":
    # Petit test rapide pour vérifier que ça marche
    print("🧪 Tests rapides du module resilience.py\n")

    test_data = pd.DataFrame({
        "region_id": ["MUPL", "MUPW", "MUBL"],
        "region_name": ["Port Louis", "Plaines Wilhems", "Black River"],
        "exposure": [78, 60, 80],
        "vulnerability": [70, 68, 60],
        "adaptation": [65, 70, 55],
    })

    print("Data initiale :")
    print(test_data, "\n")

    print("➡ Calcul des indices de résilience :")
    res_df = calculate_resilience_batch(test_data)
    res_df = add_resilience_category_column(res_df)
    print(res_df[["region_name", "exposure", "vulnerability", "adaptation", "resilience_index", "resilience_category"]], "\n")

    print("➡ Simulation cyclone (severity=50) :")
    sim_df = simulate_cyclone_impact(test_data, severity=50)
    print(sim_df[["region_name", "exposure", "resilience_index"]])
