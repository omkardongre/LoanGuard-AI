"""
Monte Carlo Simulation Engine for Portfolio Risk.
V9 NEW - VaR/CVaR calculations with advanced analytics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime


@dataclass
class VaRResult:
    """Value at Risk calculation result."""
    confidence_level: float
    var_amount: float
    var_pct_of_portfolio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence_level_pct": round(self.confidence_level * 100, 1),
            "var_amount": round(self.var_amount, 2),
            "var_pct_of_portfolio": round(self.var_pct_of_portfolio, 2),
        }


@dataclass
class MonteCarloResult:
    """Complete Monte Carlo simulation result."""
    simulation_id: str
    run_timestamp: str
    n_simulations: int
    seed: int
    
    # Portfolio info
    loan_count: int
    total_ead: float
    
    # VaR results
    var_95: VaRResult
    var_99: VaRResult
    
    # CVaR (Expected Shortfall)
    cvar_95: float
    cvar_99: float
    
    # Loss distribution statistics
    mean_loss: float
    median_loss: float
    std_loss: float
    min_loss: float
    max_loss: float
    
    # Percentiles
    percentiles: Dict[str, float]
    
    # Loss distribution (binned for visualization)
    loss_histogram: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_info": {
                "id": self.simulation_id,
                "timestamp": self.run_timestamp,
                "n_simulations": self.n_simulations,
                "seed": self.seed,
            },
            "portfolio": {
                "loan_count": self.loan_count,
                "total_ead": round(self.total_ead, 2),
            },
            "var": {
                "var_95": self.var_95.to_dict(),
                "var_99": self.var_99.to_dict(),
            },
            "cvar": {
                "cvar_95_amount": round(self.cvar_95, 2),
                "cvar_99_amount": round(self.cvar_99, 2),
                "cvar_95_pct": round(self.cvar_95 / self.total_ead * 100, 2) if self.total_ead > 0 else 0,
                "cvar_99_pct": round(self.cvar_99 / self.total_ead * 100, 2) if self.total_ead > 0 else 0,
            },
            "loss_distribution": {
                "mean": round(self.mean_loss, 2),
                "median": round(self.median_loss, 2),
                "std": round(self.std_loss, 2),
                "min": round(self.min_loss, 2),
                "max": round(self.max_loss, 2),
            },
            "percentiles": {k: round(v, 2) for k, v in self.percentiles.items()},
            "histogram": self.loss_histogram,
        }


class MonteCarloSimulator:
    """
    Production-level Monte Carlo simulation for credit portfolio risk.
    
    Calculates:
    - VaR (Value at Risk) at various confidence levels
    - CVaR (Conditional VaR / Expected Shortfall)
    - Loss distribution statistics
    """
    
    DEFAULT_SIMULATIONS = 10000
    DEFAULT_SEED = 42
    
    def __init__(
        self,
        n_simulations: int = DEFAULT_SIMULATIONS,
        seed: int = DEFAULT_SEED,
    ):
        self.n_simulations = n_simulations
        self.seed = seed
        self.rng = np.random.RandomState(seed)
    
    def simulate_portfolio_losses(
        self,
        loans: List[Dict[str, Any]],
        correlation: float = 0.2,
    ) -> np.ndarray:
        """
        Simulate portfolio losses using single-factor Gaussian copula model.
        
        This is the industry-standard approach for credit portfolio simulation.
        
        Args:
            loans: List of loans with pd, lgd, ead
            correlation: Asset correlation parameter (default 0.2 = Basel IRB)
            
        Returns:
            Array of simulated portfolio losses (one per simulation)
        """
        n_loans = len(loans)
        
        # Extract loan parameters
        pds = np.array([loan.get("breach_probability", loan.get("pd", 0.1)) for loan in loans])
        lgds = np.array([loan.get("lgd", 0.45) for loan in loans])
        eads = np.array([loan.get("facility_amount", loan.get("ead", 0)) for loan in loans])
        
        # Convert PDs to default thresholds (inverse normal)
        thresholds = self._norm_inv(pds)
        
        # Simulate correlated asset values using single-factor model
        # Asset value = sqrt(correlation) * Z + sqrt(1-correlation) * epsilon
        # where Z is systematic factor and epsilon is idiosyncratic factor
        
        # Systematic factors (one per simulation)
        Z = self.rng.standard_normal(self.n_simulations)
        
        # Idiosyncratic factors (one per loan per simulation)
        epsilon = self.rng.standard_normal((self.n_simulations, n_loans))
        
        # Correlated asset values
        sqrt_rho = np.sqrt(correlation)
        sqrt_one_minus_rho = np.sqrt(1 - correlation)
        
        asset_values = sqrt_rho * Z[:, np.newaxis] + sqrt_one_minus_rho * epsilon
        
        # Default indicator: asset value < threshold
        defaults = asset_values < thresholds
        
        # Calculate losses
        # Loss = default_indicator * LGD * EAD
        losses = defaults * lgds * eads
        
        # Sum across loans for each simulation
        portfolio_losses = losses.sum(axis=1)
        
        return portfolio_losses
    
    def _norm_inv(self, p: np.ndarray) -> np.ndarray:
        """Inverse standard normal CDF (probit function)."""
        from scipy import stats
        return stats.norm.ppf(np.clip(p, 1e-10, 1-1e-10))
    
    def calculate_var(
        self,
        losses: np.ndarray,
        confidence_level: float,
        total_ead: float,
    ) -> VaRResult:
        """Calculate Value at Risk at given confidence level."""
        var_amount = np.percentile(losses, confidence_level * 100)
        var_pct = (var_amount / total_ead * 100) if total_ead > 0 else 0
        
        return VaRResult(
            confidence_level=confidence_level,
            var_amount=var_amount,
            var_pct_of_portfolio=var_pct,
        )
    
    def calculate_cvar(
        self,
        losses: np.ndarray,
        confidence_level: float,
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        CVaR is the expected loss given that loss exceeds VaR.
        More informative than VaR for tail risk.
        """
        var_threshold = np.percentile(losses, confidence_level * 100)
        tail_losses = losses[losses >= var_threshold]
        
        if len(tail_losses) == 0:
            return var_threshold
        
        return np.mean(tail_losses)
    
    def create_histogram(
        self,
        losses: np.ndarray,
        n_bins: int = 20,
    ) -> List[Dict[str, Any]]:
        """Create binned histogram for visualization."""
        hist, bin_edges = np.histogram(losses, bins=n_bins)
        
        histogram = []
        for i in range(len(hist)):
            histogram.append({
                "bin_start": round(bin_edges[i], 2),
                "bin_end": round(bin_edges[i + 1], 2),
                "count": int(hist[i]),
                "frequency_pct": round(hist[i] / len(losses) * 100, 2),
            })
        
        return histogram
    
    def run_simulation(
        self,
        loans: List[Dict[str, Any]],
        correlation: float = 0.2,
    ) -> MonteCarloResult:
        """
        Run full Monte Carlo simulation on loan portfolio.
        
        Args:
            loans: List of loan dictionaries with pd, lgd, ead
            correlation: Asset correlation (0.15-0.25 typical for corporate)
            
        Returns:
            MonteCarloResult with comprehensive risk metrics
        """
        # Calculate total EAD
        total_ead = sum(loan.get("facility_amount", loan.get("ead", 0)) for loan in loans)
        
        # Run simulations
        losses = self.simulate_portfolio_losses(loans, correlation)
        
        # Calculate VaR
        var_95 = self.calculate_var(losses, 0.95, total_ead)
        var_99 = self.calculate_var(losses, 0.99, total_ead)
        
        # Calculate CVaR
        cvar_95 = self.calculate_cvar(losses, 0.95)
        cvar_99 = self.calculate_cvar(losses, 0.99)
        
        # Distribution statistics
        mean_loss = np.mean(losses)
        median_loss = np.median(losses)
        std_loss = np.std(losses)
        min_loss = np.min(losses)
        max_loss = np.max(losses)
        
        # Percentiles
        percentiles = {
            "p50": float(np.percentile(losses, 50)),
            "p75": float(np.percentile(losses, 75)),
            "p90": float(np.percentile(losses, 90)),
            "p95": float(np.percentile(losses, 95)),
            "p99": float(np.percentile(losses, 99)),
            "p99.5": float(np.percentile(losses, 99.5)),
        }
        
        # Histogram
        histogram = self.create_histogram(losses)
        
        return MonteCarloResult(
            simulation_id=f"mc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            run_timestamp=datetime.utcnow().isoformat(),
            n_simulations=self.n_simulations,
            seed=self.seed,
            loan_count=len(loans),
            total_ead=total_ead,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            mean_loss=mean_loss,
            median_loss=median_loss,
            std_loss=std_loss,
            min_loss=min_loss,
            max_loss=max_loss,
            percentiles=percentiles,
            loss_histogram=histogram,
        )
    
    def run_stressed_simulation(
        self,
        loans: List[Dict[str, Any]],
        pd_multiplier: float = 1.0,
        lgd_multiplier: float = 1.0,
        correlation_stress: float = 0.0,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo with stressed parameters.
        
        Args:
            loans: Loan portfolio
            pd_multiplier: Stress multiplier for PD
            lgd_multiplier: Stress multiplier for LGD
            correlation_stress: Additional correlation during stress
        """
        # Apply stress to loans
        stressed_loans = []
        for loan in loans:
            stressed_loan = loan.copy()
            base_pd = loan.get("breach_probability", loan.get("pd", 0.1))
            base_lgd = loan.get("lgd", 0.45)
            
            stressed_loan["breach_probability"] = min(1.0, base_pd * pd_multiplier)
            stressed_loan["lgd"] = min(1.0, base_lgd * lgd_multiplier)
            stressed_loans.append(stressed_loan)
        
        # Stressed correlation (correlations increase during crisis)
        base_correlation = 0.2
        stressed_correlation = min(0.5, base_correlation + correlation_stress)
        
        return self.run_simulation(stressed_loans, correlation=stressed_correlation)
    
    def compare_scenarios(
        self,
        loans: List[Dict[str, Any]],
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compare VaR/CVaR across multiple stress scenarios.
        
        Args:
            loans: Base loan portfolio
            scenarios: List of scenario dicts with {name, pd_multiplier, lgd_multiplier}
        """
        results = {}
        
        # Base case
        base_result = self.run_simulation(loans)
        results["base"] = {
            "name": "Base Case",
            "var_95": base_result.var_95.var_amount,
            "var_99": base_result.var_99.var_amount,
            "cvar_99": base_result.cvar_99,
            "mean_loss": base_result.mean_loss,
        }
        
        # Stressed scenarios
        for scenario in scenarios:
            scenario_name = scenario.get("name", "unnamed")
            pd_mult = scenario.get("pd_multiplier", 1.0)
            lgd_mult = scenario.get("lgd_multiplier", 1.0)
            corr_stress = scenario.get("correlation_stress", 0.0)
            
            stressed_result = self.run_stressed_simulation(
                loans, pd_mult, lgd_mult, corr_stress
            )
            
            results[scenario_name] = {
                "name": scenario_name,
                "var_95": stressed_result.var_95.var_amount,
                "var_99": stressed_result.var_99.var_amount,
                "cvar_99": stressed_result.cvar_99,
                "mean_loss": stressed_result.mean_loss,
                "var_99_increase_pct": round(
                    (stressed_result.var_99.var_amount - base_result.var_99.var_amount) /
                    base_result.var_99.var_amount * 100, 2
                ) if base_result.var_99.var_amount > 0 else 0,
            }
        
        return {
            "comparison": results,
            "worst_case": max(
                results.keys(),
                key=lambda k: results[k]["var_99"]
            ),
            "total_scenarios": len(results),
        }


# Singleton instance
_monte_carlo_simulator: Optional[MonteCarloSimulator] = None


def get_monte_carlo_simulator(
    n_simulations: int = 10000,
    seed: int = 42,
) -> MonteCarloSimulator:
    """Get or create MonteCarloSimulator singleton."""
    global _monte_carlo_simulator
    if _monte_carlo_simulator is None:
        _monte_carlo_simulator = MonteCarloSimulator(n_simulations, seed)
    return _monte_carlo_simulator
