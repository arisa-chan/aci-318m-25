# -*- coding: utf-8 -*-

"""
ACI 318M-25 Footing Design Library
Building Code Requirements for Structural Concrete - Foundation Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 13: Foundations
- Chapter 16: Strut-and-Tie Models
- Chapter 22: Shear and Torsion

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.0
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties

class FootingType(Enum):
    """Types of footings"""
    ISOLATED_SQUARE = "isolated_square"
    ISOLATED_RECTANGULAR = "isolated_rectangular"
    COMBINED = "combined"
    STRAP = "strap"
    MAT = "mat"
    PILE_CAP = "pile_cap"

class SoilCondition(Enum):
    """Soil bearing conditions"""
    ALLOWABLE_STRESS = "allowable_stress"
    ULTIMATE_BEARING = "ultimate_bearing"
    SETTLEMENT_CONTROLLED = "settlement_controlled"

@dataclass
class FootingGeometry:
    """Footing geometry properties"""
    length: float             # Footing length (mm)
    width: float              # Footing width (mm)
    thickness: float          # Footing thickness (mm)
    cover: float              # Concrete cover (mm)
    column_width: float       # Column width (mm)
    column_depth: float       # Column depth (mm)
    footing_type: FootingType # Type of footing

@dataclass
class SoilProperties:
    """Soil properties for footing design"""
    bearing_capacity: float   # Allowable or ultimate bearing capacity (kPa)
    unit_weight: float        # Soil unit weight (kN/m³)
    friction_angle: float     # Internal friction angle (degrees)
    cohesion: float           # Soil cohesion (kPa)
    condition: SoilCondition  # Soil bearing condition type

@dataclass
class FootingLoads:
    """Footing load conditions"""
    axial_force: float        # Factored axial force (kN)
    moment_x: float           # Factored moment about x-axis (kN⋅m)
    moment_y: float           # Factored moment about y-axis (kN⋅m)
    shear_x: float            # Factored shear in x-direction (kN)
    shear_y: float            # Factored shear in y-direction (kN)
    service_axial: float      # Service axial load for bearing check (kN)
    service_moment_x: float   # Service moment x for bearing check (kN⋅m)
    service_moment_y: float   # Service moment y for bearing check (kN⋅m)
    eccentricity_x: float = 0.0  # Eccentricity x of column from footing center (mm)
    eccentricity_y: float = 0.0  # Eccentricity y of column from footing center (mm)

@dataclass
class FootingReinforcement:
    """Footing reinforcement design"""
    bottom_bars_x: str        # Bottom reinforcement in x-direction
    bottom_spacing_x: float   # Bottom bar spacing x-direction (mm)
    bottom_bars_y: str        # Bottom reinforcement in y-direction
    bottom_spacing_y: float   # Bottom bar spacing y-direction (mm)
    top_bars: str             # Top reinforcement if required
    top_spacing: float        # Top bar spacing (mm)
    development_length: float # Development length (mm)
    dowel_bars: str           # Column dowel bars
    dowel_length: float       # Dowel bar length (mm)

@dataclass
class FootingAnalysisResult:
    """Complete footing analysis results"""
    bearing_pressure: float   # Maximum bearing pressure (kPa)
    bearing_ok: bool          # Bearing capacity check result
    one_way_shear_ok: bool    # One-way shear check result
    two_way_shear_ok: bool    # Two-way (punching) shear check result
    reinforcement: FootingReinforcement
    utilization_ratio: float # Maximum utilization ratio
    design_notes: List[str]   # Design notes and warnings
    final_length: float       # Final footing length (mm)
    final_width: float        # Final footing width (mm)
    final_thickness: float    # Final footing thickness (mm)

class ACI318M25FootingDesign:
    """
    ACI 318M-25 Footing Design Library
    
    Comprehensive footing design according to ACI 318M-25:
    - Foundation design (Chapter 13)
    - Bearing pressure calculations
    - One-way and two-way shear checks
    - Flexural reinforcement design
    - Development length requirements
    """
    
    def __init__(self):
        """Initialize footing design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'flexure': 0.90,
            'shear': 0.75,
            'bearing': 0.65
        }
        
        # Minimum reinforcement requirements
        self.min_reinforcement = {
            'ratio': 0.0012,           # Minimum reinforcement ratio for footings
            'min_bar_size': 'D16',     # Minimum bar size
            'max_spacing': 450,        # Maximum bar spacing (mm)
            'min_spacing': 150         # Minimum bar spacing (mm)
        }
        
        # Design constants
        self.design_constants = {
            'bearing_reduction_factor': 0.85,  # For bearing on concrete
            'transfer_stress_factor': 0.85,    # For load transfer
            'min_footing_thickness': 150       # Minimum footing thickness (mm)
        }
    
    def calculate_required_footing_area(self, loads: FootingLoads,
                                      soil_props: SoilProperties,
                                      footing_weight_factor: float = 1.1) -> Tuple[float, float]:
        """
        Calculate required footing dimensions for bearing capacity
        
        Args:
            loads: Footing load conditions (service loads)
            soil_props: Soil properties
            footing_weight_factor: Factor to account for footing self-weight
            
        Returns:
            Tuple of (required_length, required_width) in mm
        """
        # Service loads for bearing check
        P_service = loads.service_axial
        Mx_service = loads.service_moment_x
        My_service = loads.service_moment_y
        
        # Account for footing self-weight (approximate)
        P_total = P_service * footing_weight_factor
        
        # Allowable bearing pressure
        qa = soil_props.bearing_capacity
        
        if abs(Mx_service) < 0.001 and abs(My_service) < 0.001:
            # Concentric loading
            required_area = P_total / qa  # m²
            # Assume square footing for concentric loading
            side_length = math.sqrt(required_area)
            return side_length * 1000, side_length * 1000 # Convert to mm
        else:
            # Eccentric loading - iterative approach needed
            # Start with concentric area and increase
            base_area = P_total / qa
            factor = 1.5  # Initial factor for eccentricity
            
            # Try square footing first
            B = L = math.sqrt(base_area * factor)
            
            # Check bearing pressure with eccentricity
            for iteration in range(10):
                ex = Mx_service / P_total if P_total > 0 else 0
                ey = My_service / P_total if P_total > 0 else 0
                
                # Check if eccentricity is within middle third
                if abs(ex) <= L/6 and abs(ey) <= B/6:
                    # No tension - calculate maximum pressure
                    qmax = (P_total / (B * L)) * (1 + 6*ex/L + 6*ey/B)
                    if qmax <= qa:
                        break
                
                # Increase size
                factor *= 1.2
                B = L = math.sqrt(base_area * factor)
            
            # Convert final m to mm before returning
            return L * 1000, B * 1000
    
    def calculate_bearing_pressure(self, geometry: FootingGeometry,
                                 loads: FootingLoads) -> Tuple[float, float, bool]:
        """
        Calculate bearing pressure distribution
        
        Args:
            geometry: Footing geometric properties
            loads: Footing load conditions (service loads)
            
        Returns:
            Tuple of (max_pressure_kPa, min_pressure_kPa, no_tension)
        """
        P = loads.service_axial
        Mx = loads.service_moment_x
        My = loads.service_moment_y
        
        A = geometry.length * geometry.width / 1e6  # Convert to m²
        Sx = geometry.length * geometry.width**2 / (6 * 1e9)  # Section modulus about x
        Sy = geometry.width * geometry.length**2 / (6 * 1e9)  # Section modulus about y
        
        # Bearing pressure at corners
        q_avg = P / A
        q_mx = Mx / Sx if Sx > 0 else 0
        q_my = My / Sy if Sy > 0 else 0
        
        # Corner pressures
        q1 = q_avg + q_mx + q_my  # Corner with maximum pressure
        q2 = q_avg + q_mx - q_my
        q3 = q_avg - q_mx + q_my
        q4 = q_avg - q_mx - q_my  # Corner with minimum pressure
        
        qmax = max(q1, q2, q3, q4)
        qmin = min(q1, q2, q3, q4)
        
        no_tension = qmin >= 0
        
        return qmax, qmin, no_tension
    
    def check_one_way_shear(self, geometry: FootingGeometry,
                          loads: FootingLoads,
                          material_props: MaterialProperties) -> Tuple[bool, float]:
        """
        Check one-way shear (beam shear)
        ACI 318M-25 Section 22.5
        
        Args:
            geometry: Footing geometric properties
            loads: Footing load conditions
            material_props: Material properties
            
        Returns:
            Tuple of (is_adequate, utilization_ratio)
        """
        fc_prime = material_props.fc_prime
        d = geometry.thickness - geometry.cover - 20  # Effective depth (assume 20mm bar)
        
        # Critical section at distance d from column face
        critical_distance_x = (geometry.length - geometry.column_width) / 2 - d
        critical_distance_y = (geometry.width - geometry.column_depth) / 2 - d
        
        if critical_distance_x <= 0 or critical_distance_y <= 0:
            # No critical section exists - shear is OK
            return True, 0.0
        
        # Factored bearing pressure (approximate)
        bearing_area = geometry.length * geometry.width / 1e6  # m²
        qu = loads.axial_force / bearing_area  # kPa
        
        # Shear force at critical section (both directions)
        # FIXED: Divide by 1e6 to convert mm² to m²
        Vu_x = qu * critical_distance_x * geometry.width / 1e6  # kN
        Vu_y = qu * critical_distance_y * geometry.length / 1e6  # kN
        
        # Concrete shear strength - ACI 318M-25 Eq. (22.5.5.1)
        lambda_factor = 1.0  # Normal weight concrete
        
        # Shear capacity for both directions
        Vc_x = lambda_factor * 0.17 * math.sqrt(fc_prime) * geometry.width * d / 1000  # kN
        Vc_y = lambda_factor * 0.17 * math.sqrt(fc_prime) * geometry.length * d / 1000  # kN
        
        phi = self.phi_factors['shear']
        phi_Vc_x = phi * Vc_x
        phi_Vc_y = phi * Vc_y
        
        # Check adequacy
        utilization_x = Vu_x / phi_Vc_x if phi_Vc_x > 0 else 0
        utilization_y = Vu_y / phi_Vc_y if phi_Vc_y > 0 else 0
        
        max_utilization = max(utilization_x, utilization_y)
        is_adequate = max_utilization <= 1.0
        
        return is_adequate, max_utilization
    
    def check_two_way_shear(self, geometry: FootingGeometry,
                          loads: FootingLoads,
                          material_props: MaterialProperties) -> Tuple[bool, float]:
        """
        Check two-way shear (punching shear)
        ACI 318M-25 Section 22.6
        """
        fc_prime = material_props.fc_prime
        d = geometry.thickness - geometry.cover - 20  # Effective depth
        
        # Critical section perimeter at d/2 from column face
        bo = 2 * (geometry.column_width + d) + 2 * (geometry.column_depth + d)
        
        # Punching shear force
        bearing_area = geometry.length * geometry.width / 1e6  # m²
        qu = loads.axial_force / bearing_area  # kPa
        
        # Area inside critical section
        critical_area = (geometry.column_width + d) * (geometry.column_depth + d) / 1e6  # m²
        Vu = loads.axial_force - qu * critical_area  # kN
        
        # Correctly calculate beta (ratio of long side to short side of column)
        col_max = max(geometry.column_width, geometry.column_depth)
        col_min = min(geometry.column_width, geometry.column_depth)
        beta = col_max / col_min if col_min > 0 else 1.0
        
        # Three controlling equations:
        vc1 = 0.17 * (1 + 2/beta) * math.sqrt(fc_prime)
        
        # Note: Assuming interior column (alphas = 40). 
        # For edge/corner columns, alphas drops to 30 or 20, and 'bo' calculation changes.
        alphas = 40  
        vc2 = 0.083 * (alphas * d / bo + 2) * math.sqrt(fc_prime)
        vc3 = 0.33 * math.sqrt(fc_prime)
        
        # Controlling punching shear strength
        vc = min(vc1, vc2, vc3)
        
        # Nominal punching shear capacity
        Vn = vc * bo * d / 1000  # Convert to kN
        phi = self.phi_factors['shear']
        phi_Vn = phi * Vn
        
        utilization_ratio = Vu / phi_Vn if phi_Vn > 0 else float('inf')
        is_adequate = utilization_ratio <= 1.0
        
        return is_adequate, utilization_ratio
    
    def design_flexural_reinforcement(self, geometry: FootingGeometry,
                                    loads: FootingLoads,
                                    material_props: MaterialProperties) -> FootingReinforcement:
        """
        Design flexural reinforcement for footing
        ACI 318M-25 Chapter 13
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        d = geometry.thickness - geometry.cover - 20  # Effective depth
        
        # Factored bearing pressure
        bearing_area = geometry.length * geometry.width / 1e6  # m²
        qu = loads.axial_force / bearing_area  # kPa
        
        # Critical sections for moment (at face of column)
        cantilever_x = (geometry.length - geometry.column_width) / 2  # mm
        cantilever_y = (geometry.width - geometry.column_depth) / 2   # mm
        
        # Factored moments per unit width
        Mu_x = qu * cantilever_x**2 / (2 * 1e6)  # kN⋅m/m
        Mu_y = qu * cantilever_y**2 / (2 * 1e6)  # kN⋅m/m
        
        # Design reinforcement for each direction
        As_x = self._calculate_required_steel_area(Mu_x, 1000, d, fc_prime, fy)  # per meter width
        As_y = self._calculate_required_steel_area(Mu_y, 1000, d, fc_prime, fy)  # per meter width
        
        # Correct minimum reinforcement: Shrinkage and temperature steel per ACI 318M-25
        if fy <= 420:
            rho_min = 0.0020
        elif fy <= 520:
            rho_min = 0.0018
        else:
            rho_min = 0.0018 * 420.0 / fy
            
        # As_min applies to gross section (width * thickness)
        As_min = rho_min * 1000 * geometry.thickness  # per meter width
        
        As_x = max(As_x, As_min)
        As_y = max(As_y, As_min)
        
        # Select reinforcement considering spacing limits
        bar_x, spacing_x = self._select_footing_reinforcement(
            As_x, 1000.0, fy, geometry.thickness, geometry.cover
        )
        bar_y, spacing_y = self._select_footing_reinforcement(
            As_y, 1000.0, fy, geometry.thickness, geometry.cover
        )
        
        # Development length
        development_length = self.aci.calculate_development_length(bar_x, fc_prime, fy)
        
        # Check if development length is adequate
        available_length_x = cantilever_x - geometry.cover
        available_length_y = cantilever_y - geometry.cover
        
        if development_length > min(available_length_x, available_length_y):
            # May need hooks or larger footing
            pass
        
        # Design column dowels (passing geometry to compute Ag)
        dowel_bars = self._design_column_dowels(geometry, material_props)
        dowel_length = max(development_length, 300.0)  # Minimum 300mm
        
        return FootingReinforcement(
            bottom_bars_x=bar_x,
            bottom_spacing_x=spacing_x,
            bottom_bars_y=bar_y,
            bottom_spacing_y=spacing_y,
            top_bars='None',  # Usually not required for footings
            top_spacing=0.0,
            development_length=development_length,
            dowel_bars=dowel_bars,
            dowel_length=dowel_length
        )
    
    def _calculate_required_steel_area(self, moment: float, width: float,
                                     effective_depth: float, fc_prime: float,
                                     fy: float) -> float:
        """Calculate required steel area for given moment"""
        if moment <= 0:
            return 0
        
        # Convert moment to N⋅mm
        Mu = moment * 1e6
        
        phi = self.phi_factors['flexure']
        
        # CORRECTED SIGNS
        A = phi * fy**2 / (2 * 0.85 * fc_prime * width)
        B = -phi * fy * effective_depth # Must be negative
        C = Mu                          # Must be positive
        
        discriminant = B**2 - 4*A*C
        if discriminant < 0:
            raise ValueError("Section inadequate for applied moment")
        
        # CORRECTED ROOT (Negative root for tension-controlled behavior)
        As_required = (-B - math.sqrt(discriminant)) / (2*A)
        
        return As_required
    
    def _select_footing_reinforcement(self, As_required: float, width: float,
                                      fy: float, thickness: float, cover: float,
                                      aggregate_size: float = 25.0) -> Tuple[str, float]:
        """Select appropriate bar size and spacing for footing considering ACI 318M-25 limits"""
        # Common footing bar sizes
        bar_sizes = ['D16', 'D20', 'D25', 'D28', 'D32', 'D36']
        
        # Calculate maximum spacing for crack control (ACI 318M-25 Sec. 24.3.2)
        fs = (2.0 / 3.0) * fy
        s_limit_1 = 380 * (280 / fs) - 2.5 * cover
        s_limit_2 = 300 * (280 / fs)
        max_crack_spacing = min(s_limit_1, s_limit_2)
        
        # General maximum spacing limit for footings (typically 3h or 450mm)
        max_general_spacing = min(3 * thickness, self.min_reinforcement['max_spacing'])
        
        # Governing maximum spacing
        max_spacing = min(max_crack_spacing, max_general_spacing)
        
        for bar_size in bar_sizes:
            bar_area = self.aci.get_bar_area(bar_size)
            db = self.aci.get_bar_diameter(bar_size)
            
            # Theoretical required spacing to meet area
            raw_spacing = bar_area * width / As_required
            spacing = self._round_spacing(raw_spacing)
            
            # Minimum clear spacing limits (ACI 318M-25 Sec. 25.2.1)
            min_clear_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
            min_c2c_spacing = min_clear_spacing + db
            
            if min_c2c_spacing <= spacing <= max_spacing:
                return bar_size, spacing
        
        # If no suitable spacing is found, use a standard default with maximum allowable spacing
        bar_size = 'D20'
        bar_area = self.aci.get_bar_area(bar_size)
        raw_spacing = bar_area * width / As_required
        spacing = self._round_spacing(min(max_spacing, raw_spacing))

        # Ensure spacing meets minimum requirements
        min_clear_spacing = max(25.0, self.aci.get_bar_diameter(bar_size), (4.0/3.0) * aggregate_size)
        min_c2c_spacing = min_clear_spacing + self.aci.get_bar_diameter(bar_size)
        if spacing < min_c2c_spacing:
            spacing = min_c2c_spacing

        return bar_size, spacing
    
    def _design_column_dowels(self, geometry: FootingGeometry,
                            material_props: MaterialProperties) -> str:
        """
        Design column dowel bars for load transfer
        ACI 318M-25 Section 16.3.4
        """
        # Gross area of supported column (Ag)
        Ag = geometry.column_width * geometry.column_depth
        
        # Minimum dowel area across interface is 0.005 * Ag
        As_dowel = 0.005 * Ag
        
        # Assuming a minimum of 4 dowel bars (one at each column corner)
        As_per_bar = As_dowel / 4.0
        
        # Select appropriate dowel bar size
        if As_per_bar <= self.aci.get_bar_area('D16'):
            return 'D16'
        elif As_per_bar <= self.aci.get_bar_area('D20'):
            return 'D20'
        elif As_per_bar <= self.aci.get_bar_area('D25'):
            return 'D25'
        elif As_per_bar <= self.aci.get_bar_area('D28'):
            return 'D28'
        elif As_per_bar <= self.aci.get_bar_area('D32'):
            return 'D32'
        else:
            return 'D36'
    
    def _round_len_width(self, value: float) -> float:
        """Round length/width up to nearest 100 mm."""
        return math.ceil(value / 100.0) * 100.0

    def _round_thickness(self, value: float) -> float:
        """Round thickness up to nearest 50 mm."""
        return math.ceil(value / 50.0) * 50.0

    def _round_spacing(self, value: float) -> float:
        """Round reinforcement spacing down to nearest 25 mm (minimum 25 mm)."""
        return max(25.0, math.floor(value / 25.0) * 25.0)

    def perform_complete_footing_design(self, loads: FootingLoads,
                                      soil_props: SoilProperties,
                                      material_props: MaterialProperties,
                                      initial_geometry: FootingGeometry = None) -> FootingAnalysisResult:
        """
        Perform complete footing design analysis with automatic size adjustment until utilization ≤ 1.0.
        
        Args:
            loads: Footing load conditions
            soil_props: Soil properties
            material_props: Material properties
            initial_geometry: Initial footing geometry (optional)
            
        Returns:
            Complete footing analysis results
        """
        # Determine initial geometry
        if initial_geometry is None:
            req_length, req_width = self.calculate_required_footing_area(loads, soil_props)
            length = self._round_len_width(req_length)
            width = self._round_len_width(req_width)
            thickness = max(length / 10, width / 10, self.design_constants['min_footing_thickness'])
            thickness = self._round_thickness(thickness)
            geometry = FootingGeometry(
                length=length,
                width=width,
                thickness=thickness,
                cover=75,
                column_width=400,
                column_depth=400,
                footing_type=FootingType.ISOLATED_SQUARE
            )
        else:
            geometry = initial_geometry

        max_iterations = 20
        result = None
        design_notes = []

        for iteration in range(max_iterations):
            # Bearing pressure check
            qmax, qmin, no_tension = self.calculate_bearing_pressure(geometry, loads)
            bearing_ok = qmax <= soil_props.bearing_capacity and no_tension

            # Shear checks
            one_way_ok, one_way_ratio = self.check_one_way_shear(geometry, loads, material_props)
            two_way_ok, two_way_ratio = self.check_two_way_shear(geometry, loads, material_props)

            # Reinforcement design (may fail if section too small for moment)
            try:
                reinforcement = self.design_flexural_reinforcement(geometry, loads, material_props)
            except ValueError as e:
                # Section inadequate for flexure; increase size and continue
                design_notes = [f"Iteration {iteration+1}: Flexure design failed ({str(e)}). Increasing footing size."]
                geometry = FootingGeometry(
                    length=self._round_len_width(max(geometry.length * 1.1, geometry.length + 100)),
                    width=self._round_len_width(max(geometry.width * 1.1, geometry.width + 100)),
                    thickness=self._round_thickness(max(geometry.thickness * 1.1, geometry.thickness + 50)),
                    cover=geometry.cover,
                    column_width=geometry.column_width,
                    column_depth=geometry.column_depth,
                    footing_type=geometry.footing_type
                )
                continue

            # Overall utilization
            utilization_ratio = max(
                qmax / soil_props.bearing_capacity if soil_props.bearing_capacity > 0 else 0,
                one_way_ratio,
                two_way_ratio
            )

            # Build design notes for this iteration
            design_notes = []
            if not bearing_ok:
                if qmax > soil_props.bearing_capacity:
                    design_notes.append(f"Bearing pressure {qmax:.1f} kPa exceeds capacity {soil_props.bearing_capacity:.1f} kPa")
                if not no_tension:
                    design_notes.append("Tension exists under footing - increase size or revise loading")
            if not one_way_ok:
                design_notes.append(f"One-way shear inadequate (ratio = {one_way_ratio:.2f})")
            if not two_way_ok:
                design_notes.append(f"Two-way shear inadequate (ratio = {two_way_ratio:.2f})")
            if geometry.thickness < self.design_constants['min_footing_thickness']:
                design_notes.append(f"Increase thickness to minimum {self.design_constants['min_footing_thickness']}mm")
            if reinforcement.development_length > (geometry.length - geometry.column_width) / 2 - geometry.cover:
                design_notes.append("Development length may be inadequate - consider hooks or larger footing")

            # Check if design is adequate
            if utilization_ratio <= 1.0:
                result = FootingAnalysisResult(
                    bearing_pressure=qmax,
                    bearing_ok=bearing_ok,
                    one_way_shear_ok=one_way_ok,
                    two_way_shear_ok=two_way_ok,
                    reinforcement=reinforcement,
                    utilization_ratio=utilization_ratio,
                    design_notes=design_notes,
                    final_length=geometry.length,
                    final_width=geometry.width,
                    final_thickness=geometry.thickness
                )
                break

            # Not adequate; increase footing size and iterate
            new_length = self._round_len_width(max(geometry.length * 1.1, geometry.length + 100))
            new_width = self._round_len_width(max(geometry.width * 1.1, geometry.width + 100))
            new_thickness = self._round_thickness(max(geometry.thickness * 1.1, geometry.thickness + 50))
            geometry = FootingGeometry(
                length=new_length,
                width=new_width,
                thickness=new_thickness,
                cover=geometry.cover,
                column_width=geometry.column_width,
                column_depth=geometry.column_depth,
                footing_type=geometry.footing_type
            )
        else:
            # Max iterations reached without achieving utilization ≤ 1.0
            design_notes.append("Warning: Maximum iterations reached without achieving utilization ≤ 1.0")
            result = FootingAnalysisResult(
                bearing_pressure=qmax,
                bearing_ok=bearing_ok,
                one_way_shear_ok=one_way_ok,
                two_way_shear_ok=two_way_ok,
                reinforcement=reinforcement,
                utilization_ratio=utilization_ratio,
                design_notes=design_notes,
                final_length=geometry.length,
                final_width=geometry.width,
                final_thickness=geometry.thickness
            )

        return result