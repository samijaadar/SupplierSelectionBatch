import numpy as np
import pandas as pd


def compare_supplier_rankings(df1, df2):
    required_columns = ['Supplier', 'Score']

    for df_check, name in [(df1, 'Dataset1'), (df2, 'Dataset2')]:
        missing = set(required_columns) - set(df_check.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {missing}")

    df1_sorted = df1.sort_values('Score').reset_index(drop=True)
    df2_sorted = df2.sort_values('Score').reset_index(drop=True)

    df1_sorted['Rank_Dataset1'] = np.arange(1, len(df1_sorted) + 1)
    df2_sorted['Rank_Dataset2'] = np.arange(1, len(df2_sorted) + 1)

    merged = pd.merge(
        df1_sorted[['Supplier', 'Score', 'Rank_Dataset1']],
        df2_sorted[['Supplier', 'Score', 'Rank_Dataset2']],
        on='Supplier', how='outer', suffixes=('_Dataset1', '_Dataset2')
    )

    mask = merged['Rank_Dataset1'].notna() & merged['Rank_Dataset2'].notna()
    merged['Rank_Change'] = 'N/A'
    merged.loc[mask, 'Rank_Change'] = merged.loc[mask, 'Rank_Dataset2'] - merged.loc[mask, 'Rank_Dataset1']
    merged['Score_Difference'] = merged['Score_Dataset2'] - merged['Score_Dataset1']

    for col in ['Score_Dataset1', 'Score_Dataset2', 'Rank_Dataset1', 'Rank_Dataset2', 'Score_Difference']:
        merged[col] = merged[col].fillna('Not Present')

    return merged[['Supplier', 'Score_Dataset1', 'Rank_Dataset1', 'Score_Dataset2', 'Rank_Dataset2', 'Rank_Change',
                   'Score_Difference']]

def calculate_fr(perturbation_results):
    alpha = 0.3
    beta = 0.3
    gama = 0.2
    sigma = 0.2
    rank_max = 9
    score_max = perturbation_results['Score_Difference'].abs().max()

    rank_component = (
        alpha * perturbation_results['Rank_Change'].abs() / rank_max
        + gama * perturbation_results['Rank_Dataset1'].abs() / rank_max
        + sigma * perturbation_results['Rank_Dataset2'].abs() / rank_max
        if rank_max != 0 else 0
    )

    score_component = (
        beta * perturbation_results['Score_Difference'].abs() / score_max
        if score_max != 0 else 0
    )

    rank_component = pd.to_numeric(rank_component)
    score_component = pd.to_numeric(score_component)

    # Compute FR as numeric and round to 2 decimals
    perturbation_results['FR'] = (1 - (rank_component + score_component)).round(2)
    perturbation_results = perturbation_results.sort_values(by='FR', ascending=False)

    return perturbation_results

