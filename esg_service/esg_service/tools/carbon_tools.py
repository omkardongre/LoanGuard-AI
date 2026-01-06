"""
Carbon Emissions Tracking Tools.

Production-level tools for tracking and calculating carbon emissions
for ESG-linked loans using the Climatiq API.

API Docs: https://www.climatiq.io/docs
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import requests

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Configuration
CLIMATIQ_API_KEY = os.getenv("CLIMATIQ_API_KEY", "")
CLIMATIQ_API_URL = "https://api.climatiq.io/data/v1/estimate"
CLIMATIQ_SEARCH_URL = "https://api.climatiq.io/search"


class EmissionScope(Enum):
    """GHG Protocol emission scopes."""
    SCOPE_1 = "SCOPE_1"  # Direct emissions
    SCOPE_2 = "SCOPE_2"  # Indirect from energy
    SCOPE_3 = "SCOPE_3"  # Other indirect


class ActivityCategory(Enum):
    """Common activity categories for carbon calculation."""
    ELECTRICITY = "electricity"
    FUEL = "fuel"
    TRAVEL = "travel"
    FREIGHT = "freight"
    WASTE = "waste"
    WATER = "water"
    MATERIALS = "materials"


@dataclass
class EmissionResult:
    """Result of carbon emission calculation."""
    co2e_kg: float
    co2e_tonnes: float
    co2_kg: Optional[float] = None
    ch4_kg: Optional[float] = None
    n2o_kg: Optional[float] = None
    source: str = "Climatiq"
    emission_factor_id: Optional[str] = None
    scope: Optional[str] = None
    region: Optional[str] = None
    year: Optional[int] = None


class CarbonEmissionsTracker:
    """
    Production-grade carbon emissions tracker using Climatiq API.
    
    Supports calculation of Scope 1, 2, and 3 emissions for
    ESG-linked and sustainability-linked loans.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or parameter."""
        self.api_key = api_key or CLIMATIQ_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    @property
    def available(self) -> bool:
        """Check if Climatiq API is configured."""
        return bool(self.api_key)
    
    def calculate_emissions_sync(
        self,
        activity_id: str,
        activity_value: float,
        activity_unit: str = "kWh",
        region: str = "GLOBAL",
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate carbon emissions synchronously.
        
        Args:
            activity_id: Climatiq activity ID (e.g., "electricity-supply_grid-source_residual_mix")
            activity_value: Amount of activity
            activity_unit: Unit of measurement (kWh, kg, km, etc.)
            region: Region code (e.g., "US", "GB", "GLOBAL")
            year: Emission factor year (defaults to latest)
            
        Returns:
            Dictionary with CO2e values and metadata
        """
        if not self.available:
            return {
                "success": False,
                "error": "Climatiq API not configured. Set CLIMATIQ_API_KEY.",
            }
        
        payload = {
            "emission_factor": {
                "activity_id": activity_id,
                "data_version": "^1",  # Required by Climatiq API
            },
            "parameters": {
                "energy": activity_value,
                "energy_unit": activity_unit,
            }
        }
        
        if year:
            payload["emission_factor"]["year"] = str(year)
        
        try:
            response = requests.post(
                CLIMATIQ_API_URL,
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "success": True,
                    "co2e_kg": data.get("co2e", 0),
                    "co2e_tonnes": data.get("co2e", 0) / 1000,
                    "co2_kg": data.get("constituent_gases", {}).get("co2", 0),
                    "ch4_kg": data.get("constituent_gases", {}).get("ch4", 0),
                    "n2o_kg": data.get("constituent_gases", {}).get("n2o", 0),
                    "emission_factor": {
                        "id": data.get("emission_factor", {}).get("id"),
                        "name": data.get("emission_factor", {}).get("name"),
                        "source": data.get("emission_factor", {}).get("source"),
                        "region": data.get("emission_factor", {}).get("region"),
                        "year": data.get("emission_factor", {}).get("year"),
                    },
                    "source": "Climatiq API",
                    "calculated_at": datetime.utcnow().isoformat(),
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": f"API error {response.status_code}: {error_data.get('message', 'Unknown')}",
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Climatiq API request failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def calculate_emissions_async(
        self,
        activity_id: str,
        activity_value: float,
        activity_unit: str = "kWh",
        region: str = "GLOBAL",
    ) -> Dict[str, Any]:
        """Calculate carbon emissions asynchronously."""
        if not self.available:
            return {"success": False, "error": "Climatiq API not configured"}
        
        payload = {
            "emission_factor": {
                "activity_id": activity_id,
                "data_version": "^1",
            },
            "parameters": {
                "energy": activity_value,
                "energy_unit": activity_unit,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    CLIMATIQ_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "co2e_kg": data.get("co2e", 0),
                            "co2e_tonnes": data.get("co2e", 0) / 1000,
                            "source": "Climatiq API",
                        }
                    else:
                        return {"success": False, "error": f"API error: {resp.status}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def calculate_electricity_emissions(
        self,
        kwh: float,
        country_code: str = "US",
    ) -> Dict[str, Any]:
        """
        Calculate emissions from electricity consumption.
        
        Args:
            kwh: Electricity consumption in kilowatt-hours
            country_code: ISO country code
            
        Returns:
            Emission calculation result
        """
        activity_id = "electricity-supply_grid-source_residual_mix"
        return self.calculate_emissions_sync(
            activity_id=activity_id,
            activity_value=kwh,
            activity_unit="kWh",
            region=country_code,
        )
    
    def calculate_fuel_emissions(
        self,
        liters: float,
        fuel_type: str = "diesel",
    ) -> Dict[str, Any]:
        """
        Calculate emissions from fuel combustion.
        
        Args:
            liters: Fuel consumption in liters
            fuel_type: Type of fuel (diesel, gasoline, natural_gas)
            
        Returns:
            Emission calculation result
        """
        fuel_activity_map = {
            "diesel": "fuel_type-diesel-vehicle_type_unspecified",
            "gasoline": "fuel_type-petrol-vehicle_type_unspecified",
            "petrol": "fuel_type-petrol-vehicle_type_unspecified",
            "natural_gas": "fuel_type-natural_gas-fuel_use_stationary_combustion",
        }
        
        activity_id = fuel_activity_map.get(
            fuel_type.lower(),
            "fuel_type-diesel-vehicle_type_unspecified"
        )
        
        return self.calculate_emissions_sync(
            activity_id=activity_id,
            activity_value=liters,
            activity_unit="l",
            region="GLOBAL",
        )
    
    def calculate_travel_emissions(
        self,
        kilometers: float,
        travel_type: str = "car",
    ) -> Dict[str, Any]:
        """
        Calculate emissions from travel.
        
        Args:
            kilometers: Distance traveled
            travel_type: Mode of travel (car, train, flight_domestic, flight_international)
            
        Returns:
            Emission calculation result
        """
        travel_activity_map = {
            "car": "passenger_vehicle-vehicle_type_car-fuel_source_na-distance_na-engine_size_na",
            "train": "passenger_train-route_type_commuter_rail-fuel_source_na",
            "flight_domestic": "passenger_flight-route_type_domestic-aircraft_type_na-distance_na-class_na-rf_included",
            "flight_international": "passenger_flight-route_type_international-aircraft_type_na-distance_na-class_na-rf_included",
        }
        
        activity_id = travel_activity_map.get(
            travel_type.lower(),
            "passenger_vehicle-vehicle_type_car-fuel_source_na-distance_na-engine_size_na"
        )
        
        return self.calculate_emissions_sync(
            activity_id=activity_id,
            activity_value=kilometers,
            activity_unit="km",
            region="GLOBAL",
        )
    
    def search_emission_factors(
        self,
        query: str,
        category: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for available emission factors.
        
        Args:
            query: Search query
            category: Filter by category
            region: Filter by region
            limit: Maximum results
            
        Returns:
            List of matching emission factors
        """
        if not self.available:
            return {"success": False, "error": "Climatiq API not configured"}
        
        params = {
            "query": query,
            "results_per_page": limit,
        }
        
        if category:
            params["category"] = category
        if region:
            params["region"] = region
        
        try:
            response = requests.get(
                CLIMATIQ_SEARCH_URL,
                headers=self.headers,
                params=params,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "total_results": data.get("total_results", 0),
                    "factors": [
                        {
                            "id": f.get("id"),
                            "name": f.get("name"),
                            "category": f.get("category"),
                            "source": f.get("source"),
                            "region": f.get("region"),
                            "unit": f.get("unit"),
                        }
                        for f in data.get("results", [])
                    ],
                }
            else:
                return {"success": False, "error": f"Search failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_carbon_tracker: Optional[CarbonEmissionsTracker] = None


def get_carbon_tracker() -> CarbonEmissionsTracker:
    """Get or create carbon tracker singleton."""
    global _carbon_tracker
    if _carbon_tracker is None:
        _carbon_tracker = CarbonEmissionsTracker()
    return _carbon_tracker


def calculate_carbon_emissions(
    activity_id: str,
    activity_value: float,
    activity_unit: str = "kWh",
    region: str = "GLOBAL",
) -> Dict[str, Any]:
    """
    Convenience function to calculate carbon emissions.
    
    Args:
        activity_id: Climatiq activity ID
        activity_value: Amount of activity
        activity_unit: Unit of measurement
        region: Region code
        
    Returns:
        Emission calculation result
    """
    tracker = get_carbon_tracker()
    return tracker.calculate_emissions_sync(
        activity_id=activity_id,
        activity_value=activity_value,
        activity_unit=activity_unit,
        region=region,
    )


def calculate_loan_carbon_footprint(
    loan_id: str,
    electricity_kwh: float = 0,
    fuel_liters: float = 0,
    travel_km: float = 0,
    country_code: str = "US",
) -> Dict[str, Any]:
    """
    Calculate total carbon footprint for a loan's operations.
    
    Aggregates emissions from electricity, fuel, and travel.
    
    Args:
        loan_id: Loan identifier
        electricity_kwh: Annual electricity consumption
        fuel_liters: Annual fuel consumption
        travel_km: Annual travel distance
        country_code: Country for grid emission factor
        
    Returns:
        Aggregated carbon footprint
    """
    tracker = get_carbon_tracker()
    
    if not tracker.available:
        return {"success": False, "error": "Climatiq API not configured"}
    
    total_co2e_kg = 0
    breakdown = []
    
    # Electricity emissions
    if electricity_kwh > 0:
        elec = tracker.calculate_electricity_emissions(electricity_kwh, country_code)
        if elec.get("success"):
            total_co2e_kg += elec.get("co2e_kg", 0)
            breakdown.append({
                "category": "Electricity",
                "scope": "SCOPE_2",
                "co2e_kg": elec.get("co2e_kg", 0),
                "activity_value": electricity_kwh,
                "activity_unit": "kWh",
            })
    
    # Fuel emissions
    if fuel_liters > 0:
        fuel = tracker.calculate_fuel_emissions(fuel_liters)
        if fuel.get("success"):
            total_co2e_kg += fuel.get("co2e_kg", 0)
            breakdown.append({
                "category": "Fuel",
                "scope": "SCOPE_1",
                "co2e_kg": fuel.get("co2e_kg", 0),
                "activity_value": fuel_liters,
                "activity_unit": "liters",
            })
    
    # Travel emissions
    if travel_km > 0:
        travel = tracker.calculate_travel_emissions(travel_km)
        if travel.get("success"):
            total_co2e_kg += travel.get("co2e_kg", 0)
            breakdown.append({
                "category": "Travel",
                "scope": "SCOPE_3",
                "co2e_kg": travel.get("co2e_kg", 0),
                "activity_value": travel_km,
                "activity_unit": "km",
            })
    
    return {
        "success": True,
        "loan_id": loan_id,
        "total_co2e_kg": total_co2e_kg,
        "total_co2e_tonnes": total_co2e_kg / 1000,
        "breakdown": breakdown,
        "country": country_code,
        "source": "Climatiq API",
        "calculated_at": datetime.utcnow().isoformat(),
    }


# Export
__all__ = [
    "CarbonEmissionsTracker",
    "EmissionScope",
    "ActivityCategory",
    "EmissionResult",
    "get_carbon_tracker",
    "calculate_carbon_emissions",
    "calculate_loan_carbon_footprint",
]
