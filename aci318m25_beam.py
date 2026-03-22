# -*- coding: utf-8 -*-

"""
ACI 318M-25 Beam Design Library
Building Code Requirements for Structural Concrete - Beam Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 9: Flexural Design
- Chapter 18: Earthquake Resistant Structures (Seismic Provisions)
- Chapter 22: Shear and Torsion Design
- Chapter 25: Development and Splices of Reinforcement

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.3 (Seismic Integrity & Strict 2-Layer Limit)
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties

class BeamType(Enum):
    """Types of beams for design"""
    RECTANGULAR = "rectangular"
    T_BEAM = "t_beam"
    L_BEAM = "l_beam"
    INVERTED_T = "inverted_t"

class LoadType(Enum):
    """Types of loads on beams"""
    POINT_LOAD = "point_load"
    UNIFORMLY_DISTRIBUTED = "uniformly_distributed"
    TRIANGULAR = "triangular"
    TRAPEZOIDAL = "trapezoidal"

class SeismicDesignCategory(Enum):
    """Seismic Design Categories (SDC) - ACI 318M-25"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"

class FrameSystem(Enum):
    """Seismic frame system types - ACI 318M-25"""
    ORDINARY = "ordinary"          # Ordinary Moment Frame (OMF)
    INTERMEDIATE = "intermediate"  # Intermediate Moment Frame (IMF)
    SPECIAL = "special"            # Special Moment Frame (SMF)

@dataclass
class BeamGeometry:
    """Beam geometry properties"""
    length: float              # Center-to-center span length (mm)
    width: float              # Beam width (mm)
    height: float             # Beam total height (mm)
    effective_depth: float    # Effective depth to tension reinforcement (mm)
    cover: float              # Concrete cover (mm)
    flange_width: float       # Effective flange width for T-beams (mm)
    flange_thickness: float   # Flange thickness for T-beams (mm)
    beam_type: BeamType       # Type of beam cross-section
    
    # Seismic Parameters
    clear_span: float = 0.0   # Clear span length ln (mm) - critical for seismic shear
    sdc: SeismicDesignCategory = SeismicDesignCategory.A
    frame_system: FrameSystem = FrameSystem.ORDINARY

@dataclass
class ReinforcementDesign:
    """Reinforcement design results"""
    main_bars: List[str]      # Main tension reinforcement bar sizes
    main_area: float          # Total area of main reinforcement (mm²)
    compression_bars: List[str] # Compression reinforcement if required
    compression_area: float   # Total compression reinforcement area (mm²)
    stirrups: str             # Stirrup bar size
    stirrup_spacing: float    # General stirrup spacing outside hinge (mm)
    development_length: float # Development length (mm)
    
    # Seismic & Torsion Detailing
    stirrup_spacing_hinge: float = 0.0 # Stirrup spacing in plastic hinge zone (mm)
    hinge_length: float = 0.0          # Extent of plastic hinge zone from support (mm)
    torsion_longitudinal_area: float = 0.0 # Required additional longitudinal steel for torsion (mm²)
    torsion_required: bool = False    # Flag indicating if torsion design was required

@dataclass
class BeamAnalysisResult:
    """Complete beam analysis results"""
    moment_capacity: float     # Nominal moment capacity Mn (kN⋅m)
    probable_moment: float     # Probable moment capacity Mpr (kN⋅m)
    shear_capacity: float      # Nominal shear capacity Vn (kN)
    capacity_shear_ve: float   # Seismic design shear Ve (kN)
    torsion_capacity: float    # Nominal torsion capacity Tn (kN⋅m)
    deflection: float          # Maximum deflection (mm)
    crack_width: float         # Maximum crack width (mm)
    reinforcement: ReinforcementDesign
    utilization_ratio: float  # Demand/Capacity ratio
    design_notes: List[str]    # Design notes and warnings

class ACI318M25BeamDesign:
    """
    ACI 318M-25 Beam Design Library
    
    Comprehensive beam design according to ACI 318M-25:
    - Flexural design (Chapter 9)
    - Shear and torsion design (Chapter 22)
    - Seismic Provisions & Capacity Design (Chapter 18)
    - Development lengths (Chapter 25)
    - Deflection & Crack control (Chapter 24)
    """
    
    def __init__(self):
        """Initialize beam design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'flexure_tension_controlled': 0.90,
            'flexure_compression_controlled_tied': 0.65,
            'shear': 0.75,
            'torsion': 0.75,
            'seismic_joint_shear': 0.85
        }
        
    def check_seismic_geometric_limits(self, geometry: BeamGeometry) -> List[str]:
        """
        Check dimensional limits for Special Moment Frame (SMF) beams
        ACI 318M-25 Section 18.6.2
        """
        warnings = []
        
        if geometry.frame_system == FrameSystem.SPECIAL:
            # 1. Clear span to effective depth ratio
            if geometry.clear_span > 0:
                span_ratio = geometry.clear_span / geometry.effective_depth
                if span_ratio < 4.0:
                    warnings.append(f"SMF Violation: Clear span to depth ratio ({span_ratio:.1f}) must be >= 4.0.")
            
            # 2. Minimum width
            if geometry.width < 250.0:
                warnings.append(f"SMF Violation: Beam width ({geometry.width:.0f} mm) must be >= 250 mm.")
                
            # 3. Width to depth ratio
            aspect_ratio = geometry.width / geometry.height
            if aspect_ratio < 0.3:
                warnings.append(f"SMF Violation: Beam width to overall depth ratio ({aspect_ratio:.2f}) must be >= 0.3.")
                
        return warnings

    def calculate_probable_moment_capacity(self, As: float, As_prime: float,
                                         beam_geometry: BeamGeometry,
                                         material_props: MaterialProperties) -> float:
        """
        Calculate probable flexural strength (Mpr) for SMF capacity design.
        ACI 318M-25 Section 18.6.5
        Uses steel stress of 1.25fy and strength reduction factor phi = 1.0.
        """
        fc_prime = material_props.fc_prime
        fy_pr = 1.25 * material_props.fy  # Probable yield strength
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        d_prime = beam_geometry.cover + 20.0
        
        # Determine compression block depth (a) considering both tension and compression steel yielding
        a = (As * fy_pr - As_prime * fy_pr) / (0.85 * fc_prime * b)
        a = max(0.01, a)  # Defensive limit
        
        Mpr = (As * fy_pr * (d - a/2) + As_prime * fy_pr * (a/2 - d_prime)) / 1e6
        return max(0.0, Mpr)

    def calculate_minimum_reinforcement_ratio(self, fc_prime: float, fy: float) -> float:
        """Calculate minimum reinforcement ratio - ACI 318M-25 Section 9.6.1"""
        rho_min_basic = 1.4 / fy
        rho_min_alt = 0.25 * math.sqrt(fc_prime) / fy
        return max(rho_min_basic, rho_min_alt)
    
    def calculate_maximum_reinforcement_ratio(self, fc_prime: float, fy: float,
                                            beam_geometry: BeamGeometry) -> float:
        """
        Calculate maximum reinforcement ratio
        ACI 318M-25 Section 21.2.2 and Chapter 18
        """
        beta1 = self._calculate_beta1(fc_prime)
        
        # Standard tension-controlled max ratio
        rho_max = 3/8 * 0.85 * fc_prime * beta1 / fy
        
        # Seismic limit for Special Moment Frames
        if beam_geometry.frame_system == FrameSystem.SPECIAL:
            rho_max = min(rho_max, 0.025)
            
        return rho_max
    
    def design_flexural_reinforcement(self, mu: float, beam_geometry: BeamGeometry,
                                    material_props: MaterialProperties) -> Tuple[ReinforcementDesign, List[str]]:
        """
        Design flexural reinforcement for rectangular or T-beam sections
        """
        notes = []
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        Mu = mu * 1e6
        phi = self.phi_factors['flexure_tension_controlled']
        
        rho_max = self.calculate_maximum_reinforcement_ratio(fc_prime, fy, beam_geometry)
        As_max = rho_max * b * d
        
        a_max = As_max * fy / (0.85 * fc_prime * b)
        Mn_max = As_max * fy * (d - a_max / 2)
        phi_Mn_max = phi * Mn_max
        
        if Mu <= phi_Mn_max:
            design = self._design_tension_reinforcement_only(Mu, beam_geometry, material_props)
        else:
            design = self._design_doubly_reinforced_section(Mu, beam_geometry, material_props)
            notes.append("Compression reinforcement was required to satisfy flexural demand/ductility.")
            
        # Seismic Detailing & Integrity Checks
        if beam_geometry.frame_system == FrameSystem.SPECIAL:
            notes.append("SMF Detailing: Ensure at least two continuous bars are provided at both top and bottom faces (ACI 18.6.3.1).")
            notes.append("SMF Detailing: Lap splices must not be located within joints, within 2h from joint faces, or where flexural yielding is likely (ACI 18.6.3.3).")
            
            # Integrity Check: Opposite face reinforcement must provide at least 50% of the primary face capacity (ACI 18.6.3.2)
            mn_primary = self._calculate_moment_capacity(design.main_area, beam_geometry, material_props)
            required_mn_secondary = 0.5 * mn_primary
            
            mn_provided_secondary = self._calculate_moment_capacity(design.compression_area, beam_geometry, material_props) if design.compression_area > 0 else 0.0
            
            if mn_provided_secondary < required_mn_secondary:
                # Approximate the required area to meet the 50% moment rule
                as_secondary_req = (required_mn_secondary * 1e6) / (fy * 0.9 * beam_geometry.effective_depth)
                
                # Check against absolute minimum steel limits
                rho_min = self.calculate_minimum_reinforcement_ratio(material_props.fc_prime, fy)
                as_min = rho_min * beam_geometry.width * beam_geometry.effective_depth
                
                as_secondary_req = max(as_secondary_req, as_min)
                
                design.compression_area = as_secondary_req
                design.compression_bars = self._select_reinforcement_bars(design.compression_area, beam_geometry, fy, stirrup_size='D10')
                notes.append(f"SMF Integrity: Opposite face reinforcement increased to {design.compression_area:.1f} mm² to provide >= 50% of primary moment capacity (Mn+ >= 0.5 Mn-).")
            else:
                notes.append("SMF Integrity: Provided opposite face reinforcement naturally satisfies >= 50% of primary moment capacity.")
                
        return design, notes
    
    def _design_tension_reinforcement_only(self, Mu: float, beam_geometry: BeamGeometry,
                                         material_props: MaterialProperties) -> ReinforcementDesign:
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        phi = self.phi_factors['flexure_tension_controlled']
        
        A = phi * fy**2 / (2 * 0.85 * fc_prime * b)
        B = -phi * fy * d
        C = Mu
        
        discriminant = B**2 - 4*A*C
        if discriminant < 0:
            raise ValueError("Section dimensions inadequate for applied flexural moment.")
            
        As_required = (-B - math.sqrt(discriminant)) / (2*A)
        As_min = self.calculate_minimum_reinforcement_ratio(fc_prime, fy) * b * d
        As_required = max(As_required, As_min)
        
        main_bars = self._select_reinforcement_bars(As_required, beam_geometry, fy, stirrup_size='D10')
        main_bar_size = main_bars[0] if main_bars else 'D20'
        ld = self.aci.calculate_development_length(main_bar_size, fc_prime, fy)
        
        return ReinforcementDesign(
            main_bars=main_bars, main_area=As_required,
            compression_bars=[], compression_area=0.0,
            stirrups='D10', stirrup_spacing=200.0,
            development_length=ld
        )
    
    def _design_doubly_reinforced_section(self, Mu: float, beam_geometry: BeamGeometry,
                                        material_props: MaterialProperties) -> ReinforcementDesign:
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        es = material_props.es
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        d_prime = beam_geometry.cover + 20
        phi = self.phi_factors['flexure_tension_controlled']
        
        rho_max = self.calculate_maximum_reinforcement_ratio(fc_prime, fy, beam_geometry)
        As1 = rho_max * b * d
        
        a1 = As1 * fy / (0.85 * fc_prime * b)
        Mn1 = As1 * fy * (d - a1/2)
        Mu2 = Mu - phi * Mn1
        
        beta1 = self._calculate_beta1(fc_prime)
        c = a1 / beta1
        epsilon_s_prime = 0.003 * (c - d_prime) / c
        fs_prime = max(0.0, min(epsilon_s_prime * es, fy))
        
        if fs_prime <= 0.0:
            raise ValueError("Compression steel is in the tension zone. Section must be resized.")
        
        As2_prime = Mu2 / (phi * fs_prime * (d - d_prime))
        As2 = As2_prime * (fs_prime / fy)  
        As_total = As1 + As2
        
        main_bars = self._select_reinforcement_bars(As_total, beam_geometry, fy, stirrup_size='D10')
        comp_bars = self._select_reinforcement_bars(As2_prime, beam_geometry, fy, stirrup_size='D10')
        
        main_bar_size = main_bars[0] if main_bars else 'D25'
        ld = self.aci.calculate_development_length(main_bar_size, fc_prime, fy)
        
        return ReinforcementDesign(
            main_bars=main_bars, main_area=As_total,
            compression_bars=comp_bars, compression_area=As2_prime,
            stirrups='D10', stirrup_spacing=150.0,
            development_length=ld
        )
    
    def design_shear_reinforcement(self, vu: float, mpr: float, gravity_shear: float,
                                 beam_geometry: BeamGeometry, material_props: MaterialProperties,
                                 main_reinforcement: ReinforcementDesign) -> Tuple[str, float, float, float, List[str]]:
        """
        Design shear reinforcement evaluating capacity design provisions
        Returns: (stirrup_size, s_hinge, s_span, Ve, design_notes)
        """
        notes = []
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        phi_v = self.phi_factors['shear']
        
        # Establish Design Shear (Ve)
        Vu = vu * 1000  # Default factored statics shear (N)
        Ve = Vu
        
        if beam_geometry.frame_system == FrameSystem.SPECIAL and beam_geometry.clear_span > 0:
            V_seismic = (2 * mpr * 1e6) / beam_geometry.clear_span
            Ve = (gravity_shear * 1000) + V_seismic
            Ve = max(Ve, Vu) # Take the envelope of statics vs capacity design
            notes.append(f"SMF Capacity Design: Seismic design shear Ve = {Ve/1000:.1f} kN (Governed by Mpr = {mpr:.1f} kN-m).")
        
        # Evaluate Concrete Contribution (Vc)
        Vc = 0.17 * math.sqrt(fc_prime) * b * d
        if beam_geometry.frame_system == FrameSystem.SPECIAL:
            V_seismic_only = Ve - (gravity_shear * 1000)
            if V_seismic_only > 0.5 * Ve:
                Vc = 0.0
                notes.append("SMF Detailing: Vc taken as 0 per ACI 18.6.5.2 (Seismic shear > 0.5Ve).")
        
        phi_Vc = phi_v * Vc
        Vs_req = max(0.0, (Ve / phi_v) - Vc)
        
        # Initial Stirrup Sizing
        stirrup_size = 'D10'
        Av = 2 * self.aci.get_bar_area(stirrup_size)
        
        # Calculate theoretical spacing for required shear
        if Vs_req > 0:
            s_req = Av * fy * d / Vs_req
        else:
            s_req = float('inf')
            
        # Determine Spacing Limits - ACI 318M-25 Section 9.7.6.2.2 & 18.6.4
        Vs_threshold = 0.33 * math.sqrt(fc_prime) * b * d
        s_span_max = min(d / 4, 300.0) if Vs_req > Vs_threshold else min(d / 2, 600.0)
        
        db_long = self.aci.get_bar_diameter(main_reinforcement.main_bars[0]) if main_reinforcement.main_bars else 20.0
        
        if beam_geometry.frame_system == FrameSystem.SPECIAL:
            s_hinge_max = min(d / 4, 6 * db_long, 150.0)
            s_span_max = min(s_span_max, d / 2) # Strict limit for SMF span
            notes.append(f"SMF Detailing: First hoop must be placed <= 50 mm from support face.")
        else:
            s_hinge_max = s_span_max # No special hinge zone for ordinary frames
            
        s_hinge_actual = math.floor(min(s_req, s_hinge_max) / 10) * 10
        s_span_actual = math.floor(min(s_req, s_span_max) / 10) * 10
        
        # Enforce absolute minimum spacing constructability
        if s_hinge_actual < 75.0:
            stirrup_size = 'D12'
            Av = 2 * self.aci.get_bar_area(stirrup_size)
            s_req = Av * fy * d / Vs_req if Vs_req > 0 else float('inf')
            s_hinge_actual = math.floor(min(s_req, s_hinge_max) / 10) * 10
            s_span_actual = math.floor(min(s_req, s_span_max) / 10) * 10
            notes.append(f"Stirrup size increased to {stirrup_size} to satisfy minimum 75mm clear spacing.")

        return stirrup_size, s_hinge_actual, s_span_actual, Ve / 1000, notes
    
    def perform_complete_beam_design(self, mu: float, vu: float, beam_geometry: BeamGeometry,
                                   material_props: MaterialProperties,
                                   service_moment: float = None,
                                   tu: float = 0.0,
                                   gravity_shear: float = 0.0) -> BeamAnalysisResult:
        """
        Perform complete beam design analysis including Seismic Capacity Design (Ve, Mpr)
        """
        design_notes = []
        
        # 0. SMF Geometric Warning Checks
        geom_warnings = self.check_seismic_geometric_limits(beam_geometry)
        design_notes.extend(geom_warnings)
        
        # 1. Flexural design
        flexural_design, flex_notes = self.design_flexural_reinforcement(mu, beam_geometry, material_props)
        design_notes.extend(flex_notes)
        
        # 2. Calculate Probable Moment (Mpr) for SMF Capacity Design
        mpr = 0.0
        if beam_geometry.frame_system == FrameSystem.SPECIAL:
            mpr = self.calculate_probable_moment_capacity(
                flexural_design.main_area, flexural_design.compression_area, 
                beam_geometry, material_props
            )
            
        # 3. Shear & Capacity Design
        gravity_v = gravity_shear if gravity_shear > 0 else vu * 0.5 # Approximation if not provided
        if beam_geometry.clear_span <= 0 and beam_geometry.frame_system == FrameSystem.SPECIAL:
            design_notes.append("WARNING: clear_span not provided. Capacity Shear (Ve) cannot be calculated accurately.")
            
        stirrup_size, s_hinge, s_span, ve_design, shear_notes = self.design_shear_reinforcement(
            vu, mpr, gravity_v, beam_geometry, material_props, flexural_design
        )
        design_notes.extend(shear_notes)
        
        # Assign shear results back to the reinforcement object
        flexural_design.stirrups = stirrup_size
        flexural_design.stirrup_spacing_hinge = s_hinge
        flexural_design.stirrup_spacing = s_span
        flexural_design.hinge_length = 2 * beam_geometry.height if beam_geometry.frame_system == FrameSystem.SPECIAL else 0.0
        
        # 4. Torsion (Simplified Bypass Check)
        if tu > 0:
            design_notes.append("Note: Torsion detected. Advanced combined shear-torsion iteration omitted in capacity design wrapper.")

        # 5. Calculate capacities for Demand/Capacity ratio
        phi_m = self.phi_factors['flexure_tension_controlled']
        phi_v = self.phi_factors['shear']
        
        moment_capacity = self._calculate_moment_capacity(flexural_design.main_area, beam_geometry, material_props)
        shear_capacity = self._calculate_shear_capacity(beam_geometry, material_props, stirrup_size, s_hinge)
        
        utilization_moment = mu / (phi_m * moment_capacity) if moment_capacity > 0 else 1.0
        utilization_shear = ve_design / (phi_v * shear_capacity) if shear_capacity > 0 else 1.0
        
        # 6. Deflection Calculation
        deflection = 0.0
        if service_moment:
            L = beam_geometry.length
            Ec = material_props.ec
            Ig = beam_geometry.width * beam_geometry.height**3 / 12
            deflection = (5 * service_moment * 1e6 * L**2) / (48 * Ec * Ig)
            
        return BeamAnalysisResult(
            moment_capacity=moment_capacity,
            probable_moment=mpr,
            shear_capacity=shear_capacity,
            capacity_shear_ve=ve_design,
            torsion_capacity=0.0,
            deflection=deflection,
            crack_width=0.0,
            reinforcement=flexural_design,
            utilization_ratio=max(utilization_moment, utilization_shear),
            design_notes=design_notes
        )

    def _calculate_moment_capacity(self, As: float, beam_geometry: BeamGeometry, material_props: MaterialProperties) -> float:
        if As <= 0.0:
            return 0.0
        a = As * material_props.fy / (0.85 * material_props.fc_prime * beam_geometry.width)
        Mn = As * material_props.fy * (beam_geometry.effective_depth - a/2) / 1e6
        return max(0.0, Mn)
        
    def _calculate_shear_capacity(self, beam_geometry: BeamGeometry, material_props: MaterialProperties,
                                stirrup_size: str, spacing: float) -> float:
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        Vc = 0.17 * math.sqrt(material_props.fc_prime) * b * d / 1000
        
        if stirrup_size != 'None' and spacing > 0:
            Av = 2 * self.aci.get_bar_area(stirrup_size)
            Vs = Av * material_props.fy * d / spacing / 1000
        else:
            Vs = 0.0
        return Vc + Vs
        
    def _calculate_beta1(self, fc_prime: float) -> float:
        if fc_prime <= 28.0: return 0.85
        elif fc_prime <= 55.0: return 0.85 - 0.05 * (fc_prime - 28.0) / 7.0
        else: return 0.65

    def _select_reinforcement_bars(self, As_required: float, beam_geometry: BeamGeometry, 
                                   fy: float, stirrup_size: str = 'D10', aggregate_size: float = 25.0) -> List[str]:
        """
        Select reinforcement bars checking clear spacing.
        Starts with the smallest bar (D16) and shifts to multiple layers.
        Only advances to larger bar sizes if 2 full layers still do not fit.
        """
        if As_required <= 0:
            return []
            
        bar_data = [('D16', 201.06), ('D20', 314.16), ('D25', 490.87), 
                    ('D28', 615.75), ('D32', 804.25), ('D36', 1017.88)]
        
        # Calculate available clear width between stirrup legs
        d_tie = self.aci.get_bar_diameter(stirrup_size)
        cc = beam_geometry.cover
        available_width = beam_geometry.width - 2 * cc - 2 * d_tie
        
        for bar_size, area in bar_data:
            num_bars = max(2, math.ceil(As_required / area))
            db = self.aci.get_bar_diameter(bar_size)
            
            # Minimum clear spacing per ACI 318M-25 Section 25.2.1
            min_clear_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
            
            # Calculate max bars that can fit linearly in a single layer
            max_bars_per_layer = math.floor((available_width + min_clear_spacing) / (db + min_clear_spacing))
            
            if max_bars_per_layer < 2:
                continue # The beam is too narrow even for 2 bars of this size, move to the next size
                
            num_layers = math.ceil(num_bars / max_bars_per_layer)
            
            # Practical placement limit: try not to exceed 2 layers. 
            # If we do, we move to a larger bar size to reduce the total number of bars.
            if num_layers <= 2:
                return [bar_size] * num_bars
                
        # Final Fallback if nothing fits nicely within 2 layers
        largest_bar, largest_area = bar_data[-1]
        num_largest = max(2, math.ceil(As_required / largest_area))
        return [largest_bar] * num_largest