"""
Demonstration script showing how failed trials are handled.

This script simulates what happens when Ax suggests parameters that lead to
infeasible experiments. It demonstrates:
1. Valid trials complete successfully
2. Invalid trials are marked as FAILED
3. The optimizer continues despite failures
"""

import pandas as pd
import sys
import os

# Mock the ax_client to avoid dependencies
class MockAxClient:
    """Mock AxClient for demonstration purposes."""
    
    def __init__(self):
        self.trials = []
        self.failed_trials = []
        self.completed_trials = []
    
    def mark_trial_failed(self, trial_index):
        """Mark a trial as failed."""
        self.failed_trials.append(trial_index)
        self.trials.append({
            'trial_index': trial_index,
            'trial_status': 'FAILED'
        })
    
    def complete_trial(self, trial_index, raw_data):
        """Complete a trial successfully."""
        self.completed_trials.append(trial_index)
        self.trials.append({
            'trial_index': trial_index,
            'trial_status': 'COMPLETED',
            **raw_data
        })
    
    def get_trials_data_frame(self):
        """Get dataframe of all trials."""
        return pd.DataFrame(self.trials)


def mock_virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):
    """Mock virtual experiment function."""
    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}


def mock_design_to_conc_to_vol(df, drug_stock_conc=50, drug_total_volume=0.12,
                                surfactant_stock_conc=50, surfactant_total_volume=1):
    """
    Mock version of design_to_conc_to_vol that simulates the validation.
    Raises ValueError if concentrations are too high.
    """
    # Calculate required volumes
    drug_vol_needed = (df['drug_conc'] * drug_total_volume) / drug_stock_conc
    
    # Sum of all surfactant concentrations
    s_cols = [f"s{i}" for i in range(1, 13)]
    total_surf_ratios = df[s_cols].sum(axis=1)
    surf_vol_needed = (df['surfactant_conc'] * surfactant_total_volume) / surfactant_stock_conc
    
    # Check if volumes are feasible
    dmso_vol = drug_total_volume - drug_vol_needed
    water_vol = surfactant_total_volume - surf_vol_needed
    
    if (dmso_vol < 0).any() or (water_vol < 0).any():
        raise ValueError(
            f"Invalid experimental parameters: negative volumes calculated. "
            f"DMSO: {dmso_vol.values[0]:.4f} mL, Water: {water_vol.values[0]:.4f} mL"
        )
    
    return pd.DataFrame(), pd.DataFrame()


def mock_safe_complete_trial(ax_client, trial_index, parameterization,
                              drug_stock_conc=50, drug_total_volume=0.12,
                              surfactant_stock_conc=50, surfactant_total_volume=1):
    """
    Mock version of safe_complete_trial for demonstration.
    """
    try:
        # Extract surfactant parameters
        s_params = {f"s{i}": parameterization[f"s{i}"] for i in range(1, 13)}
        
        # Run virtual experiment
        results = mock_virtual_exp(**s_params)
        
        # Create a temporary dataframe to validate volumes
        temp_df = pd.DataFrame([{
            'trial_index': trial_index,
            **s_params,
            'surfactant_conc': parameterization['surfactant_conc'],
            'drug_conc': parameterization['drug_conc']
        }])
        
        # Validate volumes (will raise ValueError if invalid)
        mock_design_to_conc_to_vol(
            temp_df,
            drug_stock_conc=drug_stock_conc,
            drug_total_volume=drug_total_volume,
            surfactant_stock_conc=surfactant_stock_conc,
            surfactant_total_volume=surfactant_total_volume
        )
        
        # If we get here, the experiment is valid
        ax_client.complete_trial(trial_index=trial_index, raw_data=results)
        return True
        
    except (ValueError, KeyError, Exception) as e:
        # Mark trial as failed
        ax_client.mark_trial_failed(trial_index=trial_index)
        print(f"  ✗ Trial {trial_index} marked as FAILED. Reason: {str(e)}")
        return False


def main():
    print("=" * 70)
    print("DEMONSTRATION: Failed Experiment Handling")
    print("=" * 70)
    
    # Create mock client
    ax_client = MockAxClient()
    
    # Test cases: mix of valid and invalid trials
    test_trials = [
        {
            'trial_index': 0,
            'description': 'Valid trial (moderate concentrations)',
            'params': {
                **{f"s{i}": 5 for i in range(1, 13)},
                'surfactant_conc': 25,
                'drug_conc': 30
            }
        },
        {
            'trial_index': 1,
            'description': 'Valid trial (low concentrations)',
            'params': {
                **{f"s{i}": 2 for i in range(1, 13)},
                'surfactant_conc': 10,
                'drug_conc': 15
            }
        },
        {
            'trial_index': 2,
            'description': 'INVALID: Drug concentration too high (requires more volume than available)',
            'params': {
                **{f"s{i}": 10 for i in range(1, 13)},
                'surfactant_conc': 30,
                'drug_conc': 100  # TOO HIGH - requires more than total volume
            }
        },
        {
            'trial_index': 3,
            'description': 'Valid trial (balanced concentrations)',
            'params': {
                **{f"s{i}": 8 for i in range(1, 13)},
                'surfactant_conc': 35,
                'drug_conc': 40
            }
        },
        {
            'trial_index': 4,
            'description': 'INVALID: Both concentrations too high',
            'params': {
                **{f"s{i}": 20 for i in range(1, 13)},
                'surfactant_conc': 100,  # TOO HIGH
                'drug_conc': 100  # TOO HIGH
            }
        },
    ]
    
    print("\nRunning trials...\n")
    
    for trial in test_trials:
        trial_index = trial['trial_index']
        description = trial['description']
        params = trial['params']
        
        print(f"Trial {trial_index}: {description}")
        print(f"  Parameters: surfactant_conc={params['surfactant_conc']}, "
              f"drug_conc={params['drug_conc']}")
        
        success = mock_safe_complete_trial(
            ax_client=ax_client,
            trial_index=trial_index,
            parameterization=params
        )
        
        if success:
            print(f"  ✓ Trial {trial_index} completed successfully\n")
        else:
            print()  # Error already printed by function
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    df = ax_client.get_trials_data_frame()
    print(f"\nTotal trials: {len(df)}")
    print(f"Completed: {len(ax_client.completed_trials)}")
    print(f"Failed: {len(ax_client.failed_trials)}")
    
    print("\nTrial Status Table:")
    print("-" * 70)
    for _, row in df.iterrows():
        idx = int(row['trial_index'])
        status = row['trial_status']
        status_symbol = "✓" if status == "COMPLETED" else "✗"
        
        if status == "COMPLETED":
            print(f"{status_symbol} Trial {idx}: {status:10s} | "
                  f"complexity={row['complexity']:.1f}, "
                  f"cost={row['cost']:.1f}, "
                  f"performance={row['performance']:.2f}")
        else:
            print(f"{status_symbol} Trial {idx}: {status:10s} | (no metrics - trial failed)")
    
    print("\n" + "=" * 70)
    print("KEY POINTS")
    print("=" * 70)
    print("""
1. Valid trials (0, 1, 3) completed successfully with metric values
2. Invalid trials (2, 4) were marked as FAILED due to infeasible parameters
3. The workflow continued despite failures
4. The optimizer can now learn to avoid problematic parameter regions
5. Failed trials don't have metric values (they're marked as FAILED)
    """)
    
    return 0 if len(ax_client.failed_trials) > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
