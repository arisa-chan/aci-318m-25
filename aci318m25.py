#! /Users/tsuno/.pyenv/shims/python3
# -*- coding: utf-8 -*-

"""
ACI 318M-25 Building Code for Structural Concrete Implementation
Based on ACI CODE-318-25 International System of Units

American Concrete Institute
Building Code Requirements for Structural Concrete (ACI 318M-25)
and Commentary (ACI 318RM-25)

@author: Enhanced by AI Assistant
@date: 2024
@version: 1.0
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ConcreteStrengthClass(Enum):
    """Concrete strength classes according to ACI 318M-25"""
    FC14 = "13.8"    # 14 MPa
    FC17 = "17.3"    # 17 MPa
    FC21 = "20.7"    # 21 MPa
    FC28 = "27.6"    # 28 MPa
    FC35 = "34.5"    # 35 MPa
    FC42 = "41.4"    # 42 MPa
    FC50 = "48.3"    # 50 MPa
    FC55 = "55.2"    # 55 MPa
    FC70 = "70"    # 70 MPa
    FC80 = "80"    # 80 MPa
    FC100 = "100"  # 100 MPa

class ReinforcementGrade(Enum):
    """Reinforcement grades according to ASTM standards used in ACI 318M-25"""
    GRADE280 = "276"   # Grade 280 (40 ksi) - fy = 280 MPa
    GRADE420 = "415"   # Grade 420 (60 ksi) - fy = 420 MPa
    GRADE520 = "520"   # Grade 520 (75 ksi) - fy = 520 MPa
    GRADE550 = "550"   # Grade 520 (80 ksi) - fy = 550 MPa

class ExposureCondition(Enum):
    """Exposure conditions for durability requirements - ACI 318M-25 Table 19.3.1.1"""
    F0 = "F0"  # Not exposed to freezing and thawing
    F1 = "F1"  # Exposed to freezing and thawing - moist conditions
    F2 = "F2"  # Exposed to freezing and thawing - with deicing chemicals
    F3 = "F3"  # Exposed to freezing and thawing - aggressive exposure
    S0 = "S0"  # Not exposed to sulfates
    S1 = "S1"  # Water-soluble sulfate (SO₄) in soil: 150-1500 ppm
    S2 = "S2"  # Water-soluble sulfate (SO₄) in soil: 1500-10000 ppm
    S3 = "S3"  # Water-soluble sulfate (SO₄) in soil: >10000 ppm
    C0 = "C0"  # Dry or protected from moisture
    C1 = "C1"  # Moist, not exposed to chlorides
    C2 = "C2"  # Exposed to chlorides from deicing chemicals, salt, brackish water

class StructuralElement(Enum):
    """Structural elements for concrete cover requirements"""
    SLAB = "slab"
    BEAM = "beam"
    COLUMN = "column"
    WALL = "wall"
    FOUNDATION = "foundation"
    JOIST = "joist"
    FOOTING = "footing"

@dataclass
class ACI318LoadCombination:
    """Load combinations according to ACI 318M-25 Section 5.3"""
    name: str
    formula: str
    description: str
    load_factors: Dict[str, float]
    category: str  # "strength" or "service"

@dataclass
class MaterialProperties:
    """Material properties according to ACI 318M-25"""
    fc_prime: float        # Specified compressive strength (MPa)
    fy: float             # Specified yield strength (MPa)
    fu: float             # Specified tensile strength (MPa)
    es: float             # Modulus of elasticity of steel (MPa)
    ec: float             # Modulus of elasticity of concrete (MPa)
    gamma_c: float        # Unit weight of concrete (kN/m³)
    description: str

class ACI318M25:
    """
    ACI 318M-25 Building Code for Structural Concrete Implementation
    
    Based on:
    - ACI CODE-318-25 International System of Units
    - Building Code Requirements for Structural Concrete and Commentary
    - American Concrete Institute (ACI)
    """
    
    def __init__(self):
        """Initialize ACI 318M-25 code implementation"""
        
        # Concrete compressive strengths (MPa) - ACI 318M-25 Section 19.2.1.1
        self.concrete_strengths = {
            ConcreteStrengthClass.FC14: {
                'fc_prime': 14.0,
                'usage': 'Plain concrete, non-structural',
                'min_cement_content': 280,  # kg/m³
                'max_w_c_ratio': 0.70
            },
            ConcreteStrengthClass.FC17: {
                'fc_prime': 17.0,
                'usage': 'Plain concrete, footings',
                'min_cement_content': 300,
                'max_w_c_ratio': 0.65
            },
            ConcreteStrengthClass.FC21: {
                'fc_prime': 21.0,
                'usage': 'Structural concrete, normal applications',
                'min_cement_content': 320,
                'max_w_c_ratio': 0.60
            },
            ConcreteStrengthClass.FC28: {
                'fc_prime': 28.0,
                'usage': 'Structural concrete, standard',
                'min_cement_content': 350,
                'max_w_c_ratio': 0.55
            },
            ConcreteStrengthClass.FC35: {
                'fc_prime': 35.0,
                'usage': 'High-strength applications',
                'min_cement_content': 375,
                'max_w_c_ratio': 0.50
            },
            ConcreteStrengthClass.FC42: {
                'fc_prime': 42.0,
                'usage': 'High-strength structural concrete',
                'min_cement_content': 400,
                'max_w_c_ratio': 0.45
            },
            ConcreteStrengthClass.FC50: {
                'fc_prime': 50.0,
                'usage': 'High-strength structural concrete',
                'min_cement_content': 425,
                'max_w_c_ratio': 0.40
            },
            ConcreteStrengthClass.FC55: {
                'fc_prime': 55.0,
                'usage': 'High-performance concrete',
                'min_cement_content': 450,
                'max_w_c_ratio': 0.38
            },
            ConcreteStrengthClass.FC70: {
                'fc_prime': 70.0,
                'usage': 'High-performance concrete',
                'min_cement_content': 475,
                'max_w_c_ratio': 0.35
            },
            ConcreteStrengthClass.FC80: {
                'fc_prime': 80.0,
                'usage': 'Ultra-high-strength concrete',
                'min_cement_content': 500,
                'max_w_c_ratio': 0.32
            },
            ConcreteStrengthClass.FC100: {
                'fc_prime': 100.0,
                'usage': 'Ultra-high-strength concrete',
                'min_cement_content': 550,
                'max_w_c_ratio': 0.28
            }
        }
        
        # Reinforcing steel properties - ACI 318M-25 Section 20.2.2.4
        self.reinforcement_grades = {
            ReinforcementGrade.GRADE280: {
                'fy': 280.0,      # Yield strength (MPa)
                'fu': 420.0,      # Tensile strength (MPa)
                'es': 200000.0,   # Modulus of elasticity (MPa)
                'grade_designation': 'Grade 280 (40 ksi)',
                'astm_specification': 'ASTM A615/A615M',
                'usage': 'Standard reinforcement for most applications'
            },
            ReinforcementGrade.GRADE420: {
                'fy': 420.0,      # Yield strength (MPa)
                'fu': 620.0,      # Tensile strength (MPa)
                'es': 200000.0,   # Modulus of elasticity (MPa)
                'grade_designation': 'Grade 420 (60 ksi)',
                'astm_specification': 'ASTM A615/A615M',
                'usage': 'Most common grade for structural concrete'
            },
            ReinforcementGrade.GRADE520: {
                'fy': 520.0,      # Yield strength (MPa)
                'fu': 690.0,      # Tensile strength (MPa)
                'es': 200000.0,   # Modulus of elasticity (MPa)
                'grade_designation': 'Grade 520 (75 ksi)',
                'astm_specification': 'ASTM A615/A615M',
                'usage': 'High-strength applications'
            },
            # --- ADDED GRADE 550 ---
            ReinforcementGrade.GRADE550: {
                'fy': 550.0,      # Yield strength (MPa)
                'fu': 725.0,      # Tensile strength (MPa) (approximate for Gr 80)
                'es': 200000.0,   # Modulus of elasticity (MPa)
                'grade_designation': 'Grade 550 (80 ksi)',
                'astm_specification': 'ASTM A615/A615M',
                'usage': 'High-strength structural applications'
            }
        }
        
        # Standard reinforcing bar sizes (PNS 49)
        self.bar_areas = {
            'D10': {'diameter': 10.0, 'area': 78.54},
            'D12': {'diameter': 12.0, 'area': 113.10},
            'D16': {'diameter': 16.0, 'area': 201.06},
            'D20': {'diameter': 20.0, 'area': 314.16},
            'D25': {'diameter': 25.0, 'area': 490.87},
            'D28': {'diameter': 28.0, 'area': 615.75},
            'D32': {'diameter': 32.0, 'area': 804.25},
            'D36': {'diameter': 36.0, 'area': 1017.88},
            'D40': {'diameter': 40.0, 'area': 1256.64},
            'D50': {'diameter': 50.0, 'area': 1963.50}
        }
        
        # Concrete cover requirements - ACI 318M-25 Table 20.5.1.3.1
        self.cover_requirements = {
            'cast_in_place': {
                StructuralElement.SLAB: {
                    'normal': 20,      # mm
                    'corrosive': 25,   # mm
                    'severe': 30       # mm
                },
                StructuralElement.BEAM: {
                    'normal': 40,      # mm (bars ≤ 35M)
                    'corrosive': 50,   # mm
                    'severe': 65       # mm
                },
                StructuralElement.COLUMN: {
                    'normal': 40,      # mm
                    'corrosive': 50,   # mm
                    'severe': 65       # mm
                },
                StructuralElement.WALL: {
                    'normal': 20,      # mm (≤ 15M bars)
                    'corrosive': 25,   # mm
                    'severe': 40       # mm
                },
                StructuralElement.FOOTING: {
                    'normal': 75,      # mm (on soil)
                    'corrosive': 100,  # mm
                    'severe': 150      # mm
                }
            },
            'precast': {
                StructuralElement.SLAB: {
                    'normal': 15,      # mm
                    'corrosive': 20,   # mm
                    'severe': 25       # mm
                },
                StructuralElement.BEAM: {
                    'normal': 25,      # mm
                    'corrosive': 40,   # mm
                    'severe': 50       # mm
                }
            }
        }
        
        # Load combinations - ACI 318M-25 Section 5.3
        self.load_combinations_strength = [
            ACI318LoadCombination(
                name="Eq. (5.3.1a)",
                formula="1.4D",
                description="Dead load only",
                load_factors={'D': 1.4, 'L': 0.0, 'Lr': 0.0, 'W': 0.0, 'E': 0.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1b)",
                formula="1.2D + 1.6L + 0.5(Lr or S or R)",
                description="Dead and live loads",
                load_factors={'D': 1.2, 'L': 1.6, 'Lr': 0.5, 'W': 0.0, 'E': 0.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1c)",
                formula="1.2D + 1.6(Lr or S or R) + (1.0L or 0.5W)",
                description="Dead and roof live loads",
                load_factors={'D': 1.2, 'L': 1.0, 'Lr': 1.6, 'W': 0.5, 'E': 0.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1d)",
                formula="1.2D + 1.0W + 1.0L + 0.5(Lr or S or R)",
                description="Dead, live, and wind loads",
                load_factors={'D': 1.2, 'L': 1.0, 'Lr': 0.5, 'W': 1.0, 'E': 0.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1e)",
                formula="1.2D + 1.0E + 1.0L + 0.2S",
                description="Dead, live, and earthquake loads",
                load_factors={'D': 1.2, 'L': 1.0, 'Lr': 0.0, 'W': 0.0, 'E': 1.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1f)",
                formula="0.9D + 1.0W",
                description="Dead and wind loads (uplift)",
                load_factors={'D': 0.9, 'L': 0.0, 'Lr': 0.0, 'W': 1.0, 'E': 0.0},
                category="strength"
            ),
            ACI318LoadCombination(
                name="Eq. (5.3.1g)",
                formula="0.9D + 1.0E",
                description="Dead and earthquake loads (uplift)",
                load_factors={'D': 0.9, 'L': 0.0, 'Lr': 0.0, 'W': 0.0, 'E': 1.0},
                category="strength"
            )
        ]
        
        # Service load combinations
        self.load_combinations_service = [
            ACI318LoadCombination(
                name="Service-1",
                formula="1.0D + 1.0L",
                description="Dead and live loads",
                load_factors={'D': 1.0, 'L': 1.0, 'Lr': 0.0, 'W': 0.0, 'E': 0.0},
                category="service"
            ),
            ACI318LoadCombination(
                name="Service-2",
                formula="1.0D + 1.0W",
                description="Dead and wind loads",
                load_factors={'D': 1.0, 'L': 0.0, 'Lr': 0.0, 'W': 1.0, 'E': 0.0},
                category="service"
            ),
            ACI318LoadCombination(
                name="Service-3",
                formula="1.0D + 1.0E",
                description="Dead and earthquake loads",
                load_factors={'D': 1.0, 'L': 0.0, 'Lr': 0.0, 'W': 0.0, 'E': 1.0},
                category="service"
            )
        ]
        
        # Strength reduction factors - ACI 318M-25 Section 21.2
        self.strength_reduction_factors = {
            'tension_controlled': 0.90,        # ϕ for tension-controlled sections
            'compression_controlled_tied': 0.65,      # ϕ for compression-controlled with ties
            'compression_controlled_spiral': 0.75,    # ϕ for compression-controlled with spirals
            'shear': 0.75,                    # ϕ for shear
            'torsion': 0.75,                  # ϕ for torsion
            'bearing': 0.65,                  # ϕ for bearing on concrete
            'plain_concrete': 0.60,           # ϕ for plain concrete
            'development': 0.75,              # ϕ for development
            'strut_and_tie': 0.75            # ϕ for strut-and-tie models
        }
        
        # Deflection limits - ACI 318M-25 Table 24.2.2
        self.deflection_limits = {
            'immediate': {
                'flat_roof': 180,              # L/180
                'floor': 360,                  # L/360
                'roof_or_floor_supporting_nonstructural': 240  # L/240
            },
            'long_term': {
                'roof_or_floor_supporting_nonstructural': 480,     # L/480
                'roof_or_floor_not_supporting_nonstructural': 240  # L/240
            }
        }

    def get_concrete_modulus(self, fc_prime: float, 
                           lambda_factor: float = 1.0, 
                           gamma_c: float = 24.0) -> float:
        """
        Calculate modulus of elasticity of concrete - ACI 318M-25 Eq. (19.2.2.1b)
        
        Args:
            fc_prime: Specified compressive strength (MPa)
            lambda_factor: Lightweight factor (1.0 for normal weight)
            gamma_c: Unit weight of concrete (kN/m³)
            
        Returns:
            Ec: Modulus of elasticity (MPa)
        """
        if gamma_c == 24.0:
            # Simplified equation for standard normal weight concrete
            ec = 4700 * math.sqrt(fc_prime) * lambda_factor
        else:
            # Convert gamma_c from kN/m³ to kg/m³ (multiplier approx. 101.97)
            w_c = gamma_c * 101.9716
            ec = (w_c ** 1.5) * 0.043 * math.sqrt(fc_prime) * lambda_factor
        
        return ec

    def get_concrete_cover(self, element: StructuralElement, 
                         exposure: str = 'normal',
                         construction_type: str = 'cast_in_place') -> Tuple[float, str, str]:
        """
        Get minimum concrete cover requirements - ACI 318M-25 Table 20.5.1.3.1
        
        Args:
            element: Structural element type
            exposure: Exposure condition ('normal', 'corrosive', 'severe')
            construction_type: 'cast_in_place' or 'precast'
            
        Returns:
            Tuple of (cover_mm, unit, description)
        """
        if construction_type in self.cover_requirements:
            if element in self.cover_requirements[construction_type]:
                cover_data = self.cover_requirements[construction_type][element]
                cover_mm = cover_data.get(exposure, cover_data['normal'])
                
                descriptions = {
                    'normal': f'{element.value} - normal exposure',
                    'corrosive': f'{element.value} - corrosive environment',
                    'severe': f'{element.value} - severe exposure'
                }
                
                return cover_mm, 'mm', descriptions.get(exposure, f'{element.value} - {exposure} exposure')
        
        # Default values if not found
        return 40.0, 'mm', f'{element.value} - default cover'

    def get_strength_reduction_factor(self, failure_mode: str) -> float:
        """
        Get strength reduction factor (φ) - ACI 318M-25 Section 21.2
        
        Args:
            failure_mode: Type of failure mode
            
        Returns:
            φ factor
        """
        return self.strength_reduction_factors.get(failure_mode, 0.75)

    def check_load_combinations(self, loads: Dict[str, float], 
                              combination_type: str = 'strength') -> List[Dict]:
        """
        Check load combinations - ACI 318M-25 Section 5.3
        
        Args:
            loads: Dictionary of loads {'D': dead, 'L': live, 'W': wind, 'E': earthquake}
            combination_type: 'strength' or 'service'
            
        Returns:
            List of combination results
        """
        if combination_type == 'strength':
            combinations = self.load_combinations_strength
        else:
            combinations = self.load_combinations_service
        
        results = []
        
        for combo in combinations:
            factored_load = 0.0
            load_details = []
            
            for load_type, factor in combo.load_factors.items():
                if load_type in loads and factor > 0:
                    contribution = factor * loads[load_type]
                    factored_load += contribution
                    if contribution > 0:
                        load_details.append(f"{factor}×{loads[load_type]:.1f}")
            
            results.append({
                'name': combo.name,
                'formula': combo.formula,
                'description': combo.description,
                'factored_load': factored_load,
                'calculation': " + ".join(load_details) if load_details else "0",
                'category': combo.category
            })
        
        return results

    def calculate_development_length(self, bar_size: str, 
                                   fc_prime: float, 
                                   fy: float,
                                   modification_factors: Dict = None) -> float:
        """
        Calculate development length for reinforcing bars - ACI 318M-25 Section 25.4
        """
        if bar_size not in self.bar_areas:
            raise ValueError(f"Unknown bar size: {bar_size}")
        
        db = self.bar_areas[bar_size]['diameter']
        
        # Default modification factors
        psi_t = modification_factors.get('top_bar', 1.0) if modification_factors else 1.0
        psi_e = modification_factors.get('epoxy', 1.0) if modification_factors else 1.0  
        psi_s = modification_factors.get('size', 1.0) if modification_factors else 1.0
        lambda_factor = modification_factors.get('lambda', 1.0) if modification_factors else 1.0
        
        # Calculate development length
        numerator = fy * psi_t * psi_e * psi_s * lambda_factor
        denominator = 25 * lambda_factor * math.sqrt(fc_prime)
        
        ld = (numerator / denominator) * db
        
        # Minimum development length is universally 300 mm for straight bars in tension
        ld_min = 300.0
        
        return max(ld, ld_min)

    def calculate_balanced_reinforcement_ratio(self, fc_prime: float, fy: float, 
                                             beta1: float = None) -> float:
        """
        Calculate balanced reinforcement ratio - ACI 318M-25 Section 22.2.2.1
        
        Args:
            fc_prime: Specified compressive strength (MPa)
            fy: Specified yield strength (MPa)
            beta1: Stress block factor (calculated if not provided)
            
        Returns:
            ρb: Balanced reinforcement ratio
        """
        if beta1 is None:
            # Calculate β1 - ACI 318M-25 Section 22.2.2.4.3
            if fc_prime <= 28:
                beta1 = 0.85
            elif fc_prime <= 55:
                beta1 = 0.85 - 0.05 * (fc_prime - 28) / 7
            else:
                beta1 = 0.65
        
        # Balanced reinforcement ratio - ACI 318M-25 Eq. (22.2.2.1)
        # ρb = (0.85 × fc' × β1 / fy) × (600 / (600 + fy))
        
        es = 200000  # Modulus of elasticity of steel (MPa)
        ecu = 0.003  # Ultimate strain of concrete
        
        # Strain in steel at balanced condition
        ey = fy / es  # Yield strain
        
        # Depth to neutral axis at balanced condition
        cb_over_d = ecu / (ecu + ey)
        
        # Balanced reinforcement ratio
        rho_b = (0.85 * fc_prime * beta1 / fy) * cb_over_d
        
        return rho_b

    def calculate_minimum_reinforcement_ratio(self, fc_prime: float, fy: float) -> float:
        """
        Calculate minimum reinforcement ratio - ACI 318M-25 Section 9.6.1.2
        
        Args:
            fc_prime: Specified compressive strength (MPa)
            fy: Specified yield strength (MPa)
            
        Returns:
            ρmin: Minimum reinforcement ratio
        """
        # ACI 318M-25 Eq. (9.6.1.2)
        # ρmin = max(1.4/fy, 0.25√fc'/fy)
        
        rho_min1 = 1.4 / fy
        rho_min2 = 0.25 * math.sqrt(fc_prime) / fy
        
        return max(rho_min1, rho_min2)

    def calculate_maximum_reinforcement_ratio(self, fc_prime: float, fy: float) -> float:
        """
        Calculate maximum reinforcement ratio for tension-controlled behavior
        ACI 318M-25 Section 21.2.2
        
        Args:
            fc_prime: Specified compressive strength (MPa)
            fy: Specified yield strength (MPa)
            
        Returns:
            ρmax: Maximum reinforcement ratio for tension-controlled behavior
        """
        # Calculate β1 - ACI 318M-25 Section 22.2.2.4.3
        if fc_prime <= 28:
            beta1 = 0.85
        elif fc_prime <= 55:
            beta1 = 0.85 - 0.05 * (fc_prime - 28) / 7
        else:
            beta1 = 0.65
            
        # For tension-controlled behavior, net tensile strain >= 0.005
        # This simplifies to 3/8 * (0.85 * fc' * beta1 / fy)
        rho_max = (3.0 / 8.0) * 0.85 * fc_prime * beta1 / fy
        
        return rho_max

    def calculate_deflection_multiplier(self, rho: float, rho_prime: float = 0.0) -> float:
        """
        Calculate deflection multiplier for long-term deflection - ACI 318M-25 Section 24.2.4.1
        
        Args:
            rho: Tension reinforcement ratio
            rho_prime: Compression reinforcement ratio
            
        Returns:
            λΔ: Deflection multiplier for sustained loads
        """
        # ACI 318M-25 Eq. (24.2.4.1.1)
        # λΔ = ξ / (1 + 50ρ')
        # where ξ = 2.0 for sustained loads lasting 5 years or more
        
        xi = 2.0  # Time-dependent factor for 5+ years
        lambda_delta = xi / (1 + 50 * rho_prime)
        
        return lambda_delta

    def calculate_effective_moment_of_inertia(self, ma: float, mcr: float, 
                                            ig: float, icr: float) -> float:
        """
        Calculate effective moment of inertia - ACI 318M-25 Section 24.2.3.5
        
        Args:
            ma: Applied moment (N⋅mm)
            mcr: Cracking moment (N⋅mm)
            ig: Gross moment of inertia (mm⁴)
            icr: Cracked moment of inertia (mm⁴)
            
        Returns:
            Ie: Effective moment of inertia (mm⁴)
        """
        # ACI 318M-25 Eq. (24.2.3.5)
        # Ie = (Mcr/Ma)³ × Ig + [1 - (Mcr/Ma)³] × Icr ≤ Ig
        
        if ma <= mcr:
            # Uncracked section
            return ig
        else:
            # Cracked section
            ratio = mcr / ma
            ie = (ratio ** 3) * ig + (1 - ratio ** 3) * icr
            return min(ie, ig)

    def calculate_cracking_moment(self, fr: float, ig: float, yt: float) -> float:
        """
        Calculate cracking moment - ACI 318M-25 Section 24.2.3.5
        
        Args:
            fr: Modulus of rupture (MPa)
            ig: Gross moment of inertia (mm⁴)
            yt: Distance from centroid to extreme tension fiber (mm)
            
        Returns:
            Mcr: Cracking moment (N⋅mm)
        """
        # ACI 318M-25 Eq. (24.2.3.5)
        # Mcr = fr × Ig / yt
        
        mcr = fr * ig / yt
        return mcr

    def calculate_modulus_of_rupture(self, fc_prime: float, lambda_factor: float = 1.0) -> float:
        """
        Calculate modulus of rupture - ACI 318M-25 Section 24.2.3.5
        
        Args:
            fc_prime: Specified compressive strength (MPa)
            lambda_factor: Lightweight factor (1.0 for normal weight)
            
        Returns:
            fr: Modulus of rupture (MPa)
        """
        # ACI 318M-25 Eq. (24.2.3.5)
        # fr = 0.62 × λ × √fc'
        
        fr = 0.62 * lambda_factor * math.sqrt(fc_prime)
        return fr

    def check_crack_control(self, fy: float, cc: float, fs: float = None) -> Dict:
        """
        Calculate maximum spacing of reinforcement for crack control.
        ACI 318M-25 Section 24.3.2
        
        Args:
            fy: Specified yield strength (MPa)
            cc: Clear cover from the nearest surface in tension to the surface 
                of the flexural tension reinforcement (mm)
            fs: Calculated stress in reinforcement at service loads (MPa). 
                If None, 2/3 fy is used per ACI 318.
            
        Returns:
            Dictionary with crack control spacing limits
        """
        if fs is None:
            fs = (2.0 / 3.0) * fy
            
        # ACI 318M-25 maximum spacing equations
        s_limit_1 = 380 * (280 / fs) - 2.5 * cc
        s_limit_2 = 300 * (280 / fs)
        
        max_spacing = min(s_limit_1, s_limit_2)
        
        return {
            'steel_stress_mpa': fs,
            'clear_cover_mm': cc,
            's_limit_1_mm': s_limit_1,
            's_limit_2_mm': s_limit_2,
            'max_spacing_mm': max_spacing
        }

    def get_material_properties(self, concrete_class: ConcreteStrengthClass, 
                              steel_grade: ReinforcementGrade) -> MaterialProperties:
        """
        Get comprehensive material properties
        
        Args:
            concrete_class: Concrete strength class
            steel_grade: Reinforcement grade
            
        Returns:
            MaterialProperties object
        """
        concrete_data = self.concrete_strengths[concrete_class]
        steel_data = self.reinforcement_grades[steel_grade]
        
        fc_prime = concrete_data['fc_prime']
        fy = steel_data['fy']
        fu = steel_data['fu']
        es = steel_data['es']
        
        # Calculate concrete modulus
        ec = self.get_concrete_modulus(fc_prime)
        
        # Standard unit weight for normal concrete
        gamma_c = 24.0  # kN/m³
        
        description = f"fc' = {fc_prime} MPa, fy = {fy} MPa"
        
        return MaterialProperties(
            fc_prime=fc_prime,
            fy=fy,
            fu=fu,
            es=es,
            ec=ec,
            gamma_c=gamma_c,
            description=description
        )

    def generate_design_summary_report(self, project_info: Dict, 
                                     concrete_class: ConcreteStrengthClass,
                                     steel_grade: ReinforcementGrade,
                                     loads: Dict[str, float],
                                     design_results: Dict = None) -> str:
        """
        Generate comprehensive design summary report
        
        Args:
            project_info: Project information dictionary
            concrete_class: Concrete strength class
            steel_grade: Reinforcement grade  
            loads: Applied loads dictionary
            design_results: Design calculation results (optional)
            
        Returns:
            Formatted report string
        """
        material_props = self.get_material_properties(concrete_class, steel_grade)
        strength_combos = self.check_load_combinations(loads, 'strength')
        service_combos = self.check_load_combinations(loads, 'service')
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                ACI 318M-25 DESIGN REPORT                            ║
║                    Building Code Requirements for Structural Concrete                ║
║                              International System of Units                          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Project Information:
{'='*80}
Project Name: {project_info.get('project_name', 'N/A')}
Location: {project_info.get('location', 'N/A')}
Date: {project_info.get('date', 'N/A')}
Engineer: {project_info.get('engineer', 'N/A')}
Element: {project_info.get('element_type', 'N/A')}

Material Properties:
{'='*80}
Concrete: {concrete_class.value} (fc' = {material_props.fc_prime} MPa)
Reinforcement: {steel_grade.value} (fy = {material_props.fy} MPa)
Concrete Modulus: Ec = {material_props.ec:.0f} MPa
Steel Modulus: Es = {material_props.es:.0f} MPa
Concrete Unit Weight: γc = {material_props.gamma_c} kN/m³

Applied Loads:
{'='*80}"""
        
        for load_type, value in loads.items():
            load_names = {
                'D': 'Dead Load',
                'L': 'Live Load',
                'Lr': 'Roof Live Load', 
                'W': 'Wind Load',
                'E': 'Earthquake Load',
                'S': 'Snow Load'
            }
            load_name = load_names.get(load_type, load_type)
            report += f"\n{load_name}: {value:.2f} kN/m²"
        
        report += f"""

Strength Design Load Combinations (ACI 318M-25 Section 5.3):
{'='*80}"""
        
        for combo in strength_combos[:5]:  # Show first 5 combinations
            report += f"\n{combo['name']}: {combo['formula']} = {combo['factored_load']:.2f} kN/m²"
        
        report += f"""

Service Load Combinations:
{'='*80}"""
        
        for combo in service_combos:
            report += f"\n{combo['name']}: {combo['formula']} = {combo['factored_load']:.2f} kN/m²"
        
        if design_results:
            report += f"""

Design Results:
{'='*80}"""
            for key, value in design_results.items():
                report += f"\n{key}: {value}"
        
        # Add reinforcement limits
        rho_min = self.calculate_minimum_reinforcement_ratio(material_props.fc_prime, material_props.fy)
        rho_max = self.calculate_maximum_reinforcement_ratio(material_props.fc_prime, material_props.fy)
        
        report += f"""

Reinforcement Ratio Limits:
{'='*80}
Minimum reinforcement ratio (ρmin): {rho_min:.4f}
Maximum reinforcement ratio (ρmax): {rho_max:.4f} (tension-controlled)

Code Compliance:
{'='*80}
Design Code: ACI 318M-25
Standard: Building Code Requirements for Structural Concrete
Units: International System of Units (SI)

Notes:
{'='*80}
1. Design based on ACI 318M-25 Building Code Requirements for Structural Concrete
2. International System of Units (SI) used throughout
3. All strength reduction factors (φ) applied per ACI 318M-25 Section 21.2
4. Load combinations per ACI 318M-25 Section 5.3
5. This analysis should be verified by a licensed structural engineer

Report generated by ACI 318M-25 Library v1.0
{'-'*80}
"""
        
        return report

    def get_bar_area(self, bar_size: str) -> float:
        """
        Get cross-sectional area of reinforcing bar
        
        Args:
            bar_size: Bar size designation (e.g., '20M', '#8')
            
        Returns:
            Cross-sectional area (mm²)
        """
        if bar_size in self.bar_areas:
            return self.bar_areas[bar_size]['area']
        else:
            raise ValueError(f"Unknown bar size: {bar_size}")

    def get_bar_diameter(self, bar_size: str) -> float:
        """
        Get diameter of reinforcing bar
        
        Args:
            bar_size: Bar size designation (e.g., '20M', '#8')
            
        Returns:
            Diameter (mm)
        """
        if bar_size in self.bar_areas:
            return self.bar_areas[bar_size]['diameter']
        else:
            raise ValueError(f"Unknown bar size: {bar_size}")

    def calculate_area_per_meter(self, bar_size: str, spacing: float) -> float:
        """
        Calculate reinforcement area per meter width
        
        Args:
            bar_size: Bar size designation
            spacing: Center-to-center spacing (mm)
            
        Returns:
            Area per meter width (mm²/m)
        """
        bar_area = self.get_bar_area(bar_size)
        area_per_meter = (bar_area * 1000) / spacing
        return area_per_meter

    def check_minimum_spacing(self, bar_size: str, aggregate_size: float = 25.0) -> float:
        """
        Check minimum bar spacing requirements - ACI 318M-25 Section 25.2
        
        Args:
            bar_size: Bar size designation
            aggregate_size: Maximum aggregate size (mm)
            
        Returns:
            Minimum spacing (mm)
        """
        db = self.get_bar_diameter(bar_size)
        
        # ACI 318M-25 Section 25.2.1
        # Minimum spacing = max(25mm, db, (4/3) × aggregate_size)
        min_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
        
        return min_spacing