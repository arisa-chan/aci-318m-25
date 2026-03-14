# -*- coding: utf-8 -*-

"""
ACI 318M-25 Wall Design Library
Building Code Requirements for Structural Concrete - Wall Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 11: Wall Design
- Chapter 14: Walls
- Chapter 18: Earthquake-Resistant Structures

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.0
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties

class WallType(Enum):
    """Types of walls"""
    BEARING_WALL = "bearing_wall"
    SHEAR_WALL = "shear_wall"
    RETAINING_WALL = "retaining_wall"
    BASEMENT_WALL = "basement_wall"
    TILT_UP_WALL = "tilt_up_wall"
    PRECAST_WALL = "precast_wall"

class WallSupportCondition(Enum):
    """Wall support conditions"""
    FIXED_TOP_BOTTOM = "fixed_top_bottom"
    PINNED_TOP_BOTTOM = "pinned_top_bottom"
    FIXED_BOTTOM_FREE_TOP = "fixed_bottom_free_top"
    CANTILEVER = "cantilever"

class LoadType(Enum):
    """Load types for wall design"""
    GRAVITY_ONLY = "gravity_only"
    LATERAL_WIND = "lateral_wind"
    LATERAL_SEISMIC = "lateral_seismic"
    SOIL_PRESSURE = "soil_pressure"
    COMBINED = "combined"

@dataclass
class WallGeometry:
    """Wall geometry properties"""
    length: float             # Wall length (mm)
    height: float             # Wall height (mm)
    thickness: float          # Wall thickness (mm)
    cover: float              # Concrete cover (mm)
    effective_length: float   # Effective length for buckling (mm)
    wall_type: WallType       # Type of wall
    support_condition: WallSupportCondition

@dataclass
class WallLoads:
    """Wall loading conditions"""
    axial_force: float        # Factored axial force per unit length (kN/m)
    in_plane_shear: float     # Factored in-plane shear (kN)
    in_plane_moment: float    # Factored in-plane moment (kN⋅m)  <-- ADDED
    out_plane_moment: float   # Factored out-of-plane moment (kN⋅m/m)
    out_plane_shear: float    # Factored out-of-plane shear (kN/m)
    lateral_pressure: float   # Lateral pressure (kPa)
    load_type: LoadType       # Type of loading

@dataclass
class WallReinforcement:
    """Wall reinforcement design"""
    vertical_bars: str        # Vertical reinforcement bar size
    vertical_spacing: float   # Vertical bar spacing (mm)
    horizontal_bars: str      # Horizontal reinforcement bar size
    horizontal_spacing: float # Horizontal bar spacing (mm)
    boundary_elements: bool   # Whether boundary elements required
    boundary_bars: str        # Boundary element longitudinal bars
    boundary_ties: str        # Boundary element ties
    tie_spacing: float        # Tie spacing in boundary elements (mm)

@dataclass
class WallAnalysisResult:
    """Complete wall analysis results"""
    axial_capacity: float     # Axial capacity (kN/m)
    shear_capacity: float     # Shear capacity (kN)
    moment_capacity: float    # Moment capacity (kN⋅m/m)
    buckling_capacity: float  # Buckling capacity (kN/m)
    reinforcement: WallReinforcement
    utilization_ratio: float # Maximum utilization ratio
    stability_ok: bool       # Stability check result
    design_notes: List[str]   # Design notes and warnings

class ACI318M25WallDesign:
    """
    ACI 318M-25 Wall Design Library
    
    Comprehensive wall design according to ACI 318M-25:
    - Bearing wall design (Chapter 11)
    - Shear wall design (Chapter 11)
    - Retaining wall design
    - Buckling and stability checks
    - Seismic design provisions (Chapter 18)
    """
    
    def __init__(self):
        """Initialize wall design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'compression_tied': 0.65,
            'compression_spiral': 0.75,
            'flexure': 0.90,
            'shear': 0.75,
            'bearing': 0.65
        }
        
        # Minimum reinforcement requirements - ACI 318M-25 Section 11.6
        self.min_reinforcement = {
            'vertical_ratio_grade420': 0.0012,      # For fy = 420 MPa
            'vertical_ratio_grade520': 0.0015,      # For fy = 520 MPa
            'horizontal_ratio': 0.0020,             # Horizontal reinforcement
            'max_spacing_vertical': 450,            # Maximum vertical bar spacing (mm)
            'max_spacing_horizontal': 450,          # Maximum horizontal bar spacing (mm)
            'min_bar_size': 'D16'                   # Minimum bar size
        }
        
        # Slenderness limits
        self.slenderness_limits = {
            'bearing_wall': 30,       # kl_u/r limit for bearing walls
            'shear_wall': 30,         # Height-to-thickness ratio for shear walls
            'cantilever_wall': 22     # Special limit for cantilever walls
        }
        
        # Boundary element requirements
        self.boundary_requirements = {
            'compression_strain_limit': 0.003,
            'neutral_axis_limit': 0.1,  # c/lw limit for boundary elements
            'min_length': 300,          # Minimum boundary element length (mm)
            'min_confinement_ratio': 0.09
        }
    
    def calculate_minimum_wall_thickness(self, geometry: WallGeometry,
                                       material_props: MaterialProperties) -> float:
        """
        Calculate minimum wall thickness requirements
        ACI 318M-25 Section 14.5
        
        Args:
            geometry: Wall geometric properties
            material_props: Material properties
            
        Returns:
            Minimum required thickness (mm)
        """
        height = geometry.height
        
        if geometry.wall_type == WallType.BEARING_WALL:
            # Bearing wall minimum thickness - ACI 318M-25 Section 14.5.3.1
            t_min_bearing = height / 25  # h/25 for bearing walls
            t_min_abs = 100              # Absolute minimum 100mm
            
        elif geometry.wall_type == WallType.SHEAR_WALL:
            # Shear wall minimum thickness - ACI 318M-25 Section 11.5.1
            t_min_shear = height / 16    # hw/16 for shear walls
            t_min_abs = 150              # Absolute minimum 150mm
            
        elif geometry.wall_type == WallType.RETAINING_WALL:
            # Retaining wall - based on height and soil pressure
            t_min_retaining = height / 12  # More conservative for lateral loads
            t_min_abs = 200              # Minimum 200mm for retaining walls
            
        else:
            # General wall requirements
            t_min_bearing = height / 30
            t_min_abs = 100
        
        t_min = max(t_min_bearing if 't_min_bearing' in locals() else t_min_shear,
                   t_min_abs)
        
        return t_min
    
    def calculate_axial_capacity(self, geometry: WallGeometry,
                               material_props: MaterialProperties,
                               vertical_steel_ratio: float) -> float:
        """
        Calculate axial capacity of wall per unit length
        ACI 318M-25 Chapter 11
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        t = geometry.thickness
        
        # Gross cross-sectional area per meter length
        Ag_per_m = t * 1000.0  # mm²/m
        
        if geometry.wall_type == WallType.BEARING_WALL:
            # Empirical design method - strictly NO steel contribution allowed
            # Slenderness reduction term: [1 - (klc / 32h)^2]
            slenderness_term = max(0.0, 1.0 - (geometry.effective_length / (32.0 * t))**2)
            Pn_per_m = 0.55 * fc_prime * Ag_per_m * slenderness_term
        else:
            # For Shear Walls, treat as a tied compression member (column)
            # NO empirical slenderness reduction is applied here.
            As_per_m = vertical_steel_ratio * Ag_per_m
            Po_per_m = 0.85 * fc_prime * (Ag_per_m - As_per_m) + fy * As_per_m
            Pn_per_m = 0.80 * Po_per_m  # Maximum nominal strength for tied members
            
        # Convert N/m to kN/m
        return max(Pn_per_m / 1000.0, 0.0)
    
    def calculate_shear_capacity(self, geometry: WallGeometry,
                               material_props: MaterialProperties,
                               horizontal_steel_ratio: float) -> float:
        """
        Calculate in-plane shear capacity of wall
        ACI 318M-25 Section 11.5.4
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        lw = geometry.length
        hw = geometry.height
        t = geometry.thickness
        
        # Effective area
        Acv = lw * t  # mm²
        
        # Determine concrete shear coefficient (alpha_c) based on aspect ratio
        if geometry.wall_type == WallType.SHEAR_WALL:
            hw_lw = hw / lw if lw > 0 else 2.0
            
            if hw_lw <= 1.5:
                alpha_c = 0.25
            elif hw_lw >= 2.0:
                alpha_c = 0.17
            else:
                # Linear interpolation between 0.25 and 0.17
                alpha_c = 0.25 - 0.08 * (hw_lw - 1.5) / 0.5
        else:
            # Standard for regular bearing walls
            alpha_c = 0.17  
            
        Vc = alpha_c * math.sqrt(fc_prime) * Acv / 1000  # kN
        
        # Steel contribution (horizontal reinforcement)
        As_h = horizontal_steel_ratio * Acv
        Vs = As_h * fy / 1000  # kN
        
        # Total shear capacity
        Vn = Vc + Vs
        
        # Maximum shear capacity limit
        Vn_max = 0.83 * math.sqrt(fc_prime) * Acv / 1000  # kN
        Vn = min(Vn, Vn_max)
        
        return Vn
    
    def calculate_out_of_plane_moment_capacity(self, geometry: WallGeometry,
                                             material_props: MaterialProperties,
                                             vertical_steel_ratio: float) -> float:
        """
        Calculate out-of-plane moment capacity
        ACI 318M-25 Chapter 9
        
        Args:
            geometry: Wall geometric properties
            material_props: Material properties
            vertical_steel_ratio: Ratio of vertical reinforcement
            
        Returns:
            Moment capacity per unit length (kN⋅m/m)
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        t = geometry.thickness
        cover = geometry.cover
        
        # Effective depth
        d = t - cover - 10  # Assume 10mm bar radius
        
        # Steel area per unit length
        As = vertical_steel_ratio * t * 1000  # mm²/m
        
        # Neutral axis depth
        a = As * fy / (0.85 * fc_prime * 1000)  # mm
        
        # Check if tension-controlled
        c = a / 0.85
        epsilon_t = 0.003 * (d - c) / c
        
        if epsilon_t >= 0.005:  # Tension-controlled
            phi = self.phi_factors['flexure']
        else:
            phi = 0.65 + (epsilon_t - 0.002) * (0.25 / 0.003)  # Transition zone
            phi = max(phi, 0.65)
        
        # Nominal moment capacity
        Mn = As * fy * (d - a/2) / 1e6  # kN⋅m/m
        
        return phi * Mn
    
    def design_vertical_reinforcement(self, geometry: WallGeometry,
                                      loads: WallLoads,
                                      material_props: MaterialProperties) -> Tuple[str, float]:
        """Design vertical reinforcement for wall including out-of-plane flexure"""
        fy = material_props.fy
        fc_prime = material_props.fc_prime
        t = geometry.thickness
        d = t - geometry.cover - 10  # approximate effective depth
        b = 1000  # per meter width
        
        # Base minimum reinforcement
        base_ratio = self.min_reinforcement['vertical_ratio_grade420'] if fy <= 420 else self.min_reinforcement['vertical_ratio_grade520']
        As_min = base_ratio * t * b
        As_required = As_min
        
        if loads.load_type != LoadType.GRAVITY_ONLY and loads.out_plane_moment > 0:
            Mu = loads.out_plane_moment * 1e6  # N-mm
            phi = self.phi_factors['flexure']
            
            # Corrected flexural quadratic formula
            A = phi * fy**2 / (2 * 0.85 * fc_prime * b)
            B = -phi * fy * d
            C = Mu
            
            discriminant = B**2 - 4*A*C
            if discriminant < 0:
                raise ValueError("Wall thickness inadequate for applied out-of-plane moment")
                
            As_moment = (-B - math.sqrt(discriminant)) / (2*A)
            As_required = max(As_min, As_moment)
            
        return self._select_wall_reinforcement(As_required, 'vertical', fy, t, geometry.cover)
    
    def design_horizontal_reinforcement(self, geometry: WallGeometry,
                                        loads: WallLoads,
                                        material_props: MaterialProperties) -> Tuple[str, float]:
        """Design horizontal reinforcement for wall"""
        fy = material_props.fy
        rho_min = self.min_reinforcement['horizontal_ratio']
        
        if loads.in_plane_shear > 0:
            Vu = loads.in_plane_shear
            fc_prime = material_props.fc_prime
            Acv = geometry.length * geometry.thickness
            
            Vc = 0.17 * math.sqrt(fc_prime) * Acv / 1000
            Vs_required = max(0, Vu / self.phi_factors['shear'] - Vc)
            
            As_shear = Vs_required * 1000 / fy  
            As_shear_ratio = As_shear / Acv
            rho_required = max(rho_min, As_shear_ratio)
        else:
            rho_required = rho_min
            
        As_required = rho_required * geometry.thickness * 1000  
        
        return self._select_wall_reinforcement(As_required, 'horizontal', fy, geometry.thickness, geometry.cover)
    
    def check_boundary_elements(self, geometry: WallGeometry,
                              loads: WallLoads,
                              material_props: MaterialProperties) -> bool:
        """
        Check if boundary elements are required using extreme fiber compressive stress
        ACI 318M-25 Section 18.10.6.3
        """
        if geometry.wall_type != WallType.SHEAR_WALL:
            return False
        
        if loads.load_type not in [LoadType.LATERAL_SEISMIC, LoadType.COMBINED]:
            return False
            
        # If the user hasn't provided an in-plane moment, we can't properly check
        if not hasattr(loads, 'in_plane_moment') or loads.in_plane_moment == 0:
            return False
        
        # Gross properties of the entire wall section
        Ag = geometry.thickness * geometry.length  # mm²
        Ig = (geometry.thickness * geometry.length**3) / 12.0  # mm⁴
        yt = geometry.length / 2.0  # Distance to extreme fiber (mm)
        
        # Convert loads to standard N and N-mm
        # loads.axial_force is kN/m. (kN/m) * mm = N
        P_N = loads.axial_force * geometry.length  
        M_Nmm = loads.in_plane_moment * 1e6
        
        # Extreme fiber compressive stress: f_c = P/A + M*y/I
        stress = (P_N / Ag) + (M_Nmm * yt / Ig)
        
        # ACI 318 limit for boundary elements: stress > 0.2 * fc'
        if stress > 0.2 * material_props.fc_prime:
            return True
            
        return False
    
    def _calculate_slenderness_factor(self, geometry: WallGeometry) -> float:
        """Calculate slenderness reduction factor"""
        klu_r = geometry.effective_length / (geometry.thickness / 3.46)  # k*lu/r
        
        if geometry.wall_type == WallType.BEARING_WALL:
            limit = self.slenderness_limits['bearing_wall']
        elif geometry.wall_type == WallType.SHEAR_WALL:
            # For shear walls, use height-to-thickness ratio
            ht_ratio = geometry.height / geometry.thickness
            if ht_ratio <= self.slenderness_limits['shear_wall']:
                return 1.0
            else:
                return max(0.7, 1.0 - (ht_ratio - 30) * 0.01)
        else:
            limit = self.slenderness_limits['cantilever_wall']
        
        if klu_r <= limit:
            return 1.0
        else:
            # Simplified reduction factor
            return max(0.5, 1.0 - (klu_r - limit) / (2 * limit))
    
    def _select_wall_reinforcement(self, As_required: float, direction: str,
                                   fy: float, thickness: float, cover: float,
                                   aggregate_size: float = 25.0) -> Tuple[str, float]:
        """Select appropriate bar size and spacing for wall"""
        bar_sizes = ['D10', 'D12', 'D16', 'D20', 'D25']
        
        # Calculate maximum spacing for crack control (ACI 318M-25 Sec. 24.3.2)
        fs = (2.0 / 3.0) * fy
        s_limit_1 = 380 * (280 / fs) - 2.5 * cover
        s_limit_2 = 300 * (280 / fs)
        max_crack_spacing = min(s_limit_1, s_limit_2)
        
        # General wall maximum spacing limit (ACI 318M-25 Sec. 11.7.2.1 / 11.7.3.1)
        if direction == 'vertical':
            max_general_spacing = min(3 * thickness, self.min_reinforcement['max_spacing_vertical'])
        else:
            max_general_spacing = min(3 * thickness, self.min_reinforcement['max_spacing_horizontal'])
            
        max_spacing = min(max_crack_spacing, max_general_spacing)
        
        for bar_size in bar_sizes:
            bar_area = self.aci.get_bar_area(bar_size)
            db = self.aci.get_bar_diameter(bar_size)
            
            spacing = bar_area * 1000 / As_required 
            
            # Minimum clear spacing limits
            min_clear_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
            min_c2c_spacing = min_clear_spacing + db
            
            if min_c2c_spacing <= spacing <= max_spacing:
                return bar_size, spacing
        
        bar_size = 'D12'
        bar_area = self.aci.get_bar_area(bar_size)
        spacing = min(max_spacing, bar_area * 1000 / As_required)
        
        return bar_size, spacing
    
    def perform_complete_wall_design(self, geometry: WallGeometry,
                                   loads: WallLoads,
                                   material_props: MaterialProperties) -> WallAnalysisResult:
        """
        Perform complete wall design analysis
        
        Args:
            geometry: Wall geometric properties
            loads: Wall loading conditions
            material_props: Material properties
            
        Returns:
            Complete wall analysis results
        """
        design_notes = []
        
        # Check minimum thickness
        t_min = self.calculate_minimum_wall_thickness(geometry, material_props)
        if geometry.thickness < t_min:
            design_notes.append(f"Increase thickness to minimum {t_min:.0f}mm")
        
        # Design reinforcement
        vert_bar, vert_spacing = self.design_vertical_reinforcement(geometry, loads, material_props)
        horiz_bar, horiz_spacing = self.design_horizontal_reinforcement(geometry, loads, material_props)
        
        # Calculate steel ratios
        vert_steel_ratio = self.aci.get_bar_area(vert_bar) / (vert_spacing * geometry.thickness)
        horiz_steel_ratio = self.aci.get_bar_area(horiz_bar) / (horiz_spacing * geometry.thickness)
        
        # Calculate capacities
        axial_capacity = self.calculate_axial_capacity(geometry, material_props, vert_steel_ratio)
        shear_capacity = self.calculate_shear_capacity(geometry, material_props, horiz_steel_ratio)
        moment_capacity = self.calculate_out_of_plane_moment_capacity(geometry, material_props, vert_steel_ratio)
        
        # Buckling capacity
        if geometry.wall_type == WallType.BEARING_WALL:
            # The empirical method inside calculate_axial_capacity already applies the slenderness reduction
            buckling_capacity = axial_capacity
            slenderness_factor = 1.0 # Reset for the subsequent stability check logic to prevent a double penalty
        else:
            # For shear walls treated as compression members, apply macroscopic buckling reduction here
            slenderness_factor = self._calculate_slenderness_factor(geometry)
            buckling_capacity = axial_capacity * slenderness_factor
        
        # Check boundary elements
        boundary_required = self.check_boundary_elements(geometry, loads, material_props)
        
        # Design boundary elements if required
        if boundary_required:
            boundary_bars = 'D20'  # Simplified
            boundary_ties = 'D10'
            tie_spacing = 100.0    # Close spacing for confinement
            design_notes.append("Boundary elements required for seismic design")
        else:
            boundary_bars = 'None'
            boundary_ties = 'None'
            tie_spacing = 0.0
        
        # Calculate utilization ratios
        utilization_axial = abs(loads.axial_force) / axial_capacity if axial_capacity > 0 else 0
        utilization_shear = abs(loads.in_plane_shear) / (self.phi_factors['shear'] * shear_capacity) if shear_capacity > 0 else 0
        utilization_moment = abs(loads.out_plane_moment) / moment_capacity if moment_capacity > 0 else 0
        
        utilization_ratio = max(utilization_axial, utilization_shear, utilization_moment)
        
        # Stability check
        stability_ok = utilization_ratio <= 1.0 and slenderness_factor > 0.5
        
        if not stability_ok:
            design_notes.append("Stability concerns - check slenderness and loading")
        
        if utilization_ratio > 1.0:
            design_notes.append("Design inadequate - increase section or reinforcement")
        
        # Create result objects
        reinforcement = WallReinforcement(
            vertical_bars=vert_bar,
            vertical_spacing=vert_spacing,
            horizontal_bars=horiz_bar,
            horizontal_spacing=horiz_spacing,
            boundary_elements=boundary_required,
            boundary_bars=boundary_bars,
            boundary_ties=boundary_ties,
            tie_spacing=tie_spacing
        )
        
        return WallAnalysisResult(
            axial_capacity=axial_capacity,
            shear_capacity=shear_capacity,
            moment_capacity=moment_capacity,
            buckling_capacity=buckling_capacity,
            reinforcement=reinforcement,
            utilization_ratio=utilization_ratio,
            stability_ok=stability_ok,
            design_notes=design_notes
        )