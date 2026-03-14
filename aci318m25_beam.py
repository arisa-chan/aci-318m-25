# -*- coding: utf-8 -*-

"""
ACI 318M-25 Beam Design Library
Building Code Requirements for Structural Concrete - Beam Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 9: Flexural Design
- Chapter 22: Shear and Torsion Design
- Chapter 25: Development and Splices of Reinforcement

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.0
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

@dataclass
class BeamGeometry:
    """Beam geometry properties"""
    length: float              # Beam length (mm)
    width: float              # Beam width (mm)
    height: float             # Beam total height (mm)
    effective_depth: float    # Effective depth to tension reinforcement (mm)
    cover: float              # Concrete cover (mm)
    flange_width: float       # Effective flange width for T-beams (mm)
    flange_thickness: float   # Flange thickness for T-beams (mm)
    beam_type: BeamType       # Type of beam cross-section

@dataclass
class ReinforcementDesign:
    """Reinforcement design results"""
    main_bars: List[str]      # Main tension reinforcement bar sizes
    main_area: float          # Total area of main reinforcement (mm²)
    compression_bars: List[str] # Compression reinforcement if required
    compression_area: float   # Total compression reinforcement area (mm²)
    stirrups: str             # Stirrup bar size
    stirrup_spacing: float    # Stirrup spacing (mm)
    development_length: float # Development length (mm)
    # --- New Torsion Fields ---
    torsion_longitudinal_area: float = 0.0 # Required additional longitudinal steel for torsion (mm²)
    torsion_required: bool = False    # Flag indicating if torsion design was required

@dataclass
class BeamAnalysisResult:
    """Complete beam analysis results"""
    moment_capacity: float     # Nominal moment capacity Mn (kN⋅m)
    shear_capacity: float      # Nominal shear capacity Vn (kN)
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
    - Development lengths (Chapter 25)
    - Deflection control (Chapter 24)
    - Crack control (Chapter 24)
    """
    
    def __init__(self):
        """Initialize beam design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'flexure_tension_controlled': 0.90,
            'flexure_compression_controlled_tied': 0.65,
            'flexure_compression_controlled_spiral': 0.75,
            'shear': 0.75,
            'torsion': 0.75,
            'bearing': 0.65
        }
        
        # Minimum reinforcement ratios - ACI 318M-25 Section 9.6.1
        self.rho_min_factors = {
            'normal': 1.4,  # 1.4/fy for normal sections
            'flanged': 1.4  # Special provisions for flanged sections
        }
        
        # Maximum aggregate size factors for development length
        self.development_factors = {
            'clear_spacing_factor': 1.0,    # Based on clear spacing
            'transverse_reinforcement': 1.0, # Based on transverse steel
            'confinement_factor': 1.0        # Confinement effects
        }
    
    def calculate_effective_flange_width(self, beam_geometry: BeamGeometry, 
                                       span_length: float) -> float:
        """
        Calculate effective flange width for T-beams
        ACI 318M-25 Section 6.3.2
        
        Args:
            beam_geometry: Beam geometric properties
            span_length: Clear span length (mm)
            
        Returns:
            Effective flange width (mm)
        """
        bw = beam_geometry.width
        hf = beam_geometry.flange_thickness
        
        # ACI 318M-25 Section 6.3.2.1 - effective width limitations
        be1 = span_length / 4.0  # One-quarter of span length
        be2 = bw + 16 * hf       # Beam width plus 16 times flange thickness
        be3 = beam_geometry.flange_width  # Given flange width
        
        effective_width = min(be1, be2, be3)
        return effective_width
    
    def calculate_minimum_reinforcement_ratio(self, fc_prime: float, fy: float,
                                            beam_type: BeamType = BeamType.RECTANGULAR) -> float:
        """
        Calculate minimum reinforcement ratio
        ACI 318M-25 Section 9.6.1
        
        Args:
            fc_prime: Concrete compressive strength (MPa)
            fy: Steel yield strength (MPa)
            beam_type: Type of beam section
            
        Returns:
            Minimum reinforcement ratio
        """
        # Basic minimum reinforcement ratio
        rho_min_basic = 1.4 / fy
        
        # Alternative minimum based on concrete strength
        rho_min_alt = 0.25 * math.sqrt(fc_prime) / fy
        
        # Use the larger value
        rho_min = max(rho_min_basic, rho_min_alt)
        
        # Special provisions for flanged sections
        if beam_type in [BeamType.T_BEAM, BeamType.L_BEAM]:
            # For flanged sections, apply to web area only
            pass  # Implementation depends on specific geometry
        
        return rho_min
    
    def calculate_maximum_reinforcement_ratio(self, fc_prime: float, fy: float,
                                            beam_geometry: BeamGeometry) -> float:
        """
        Calculate maximum reinforcement ratio for tension-controlled sections
        ACI 318M-25 Section 21.2.2
        
        Args:
            fc_prime: Concrete compressive strength (MPa)
            fy: Steel yield strength (MPa)
            beam_geometry: Beam geometric properties
            
        Returns:
            Maximum reinforcement ratio for tension-controlled sections
        """
        # Material properties
        beta1 = self._calculate_beta1(fc_prime)
        
        # Maximum reinforcement ratio
        rho_max = 3/8 * 0.85 * fc_prime * beta1 / fy
        
        return rho_max
    
    def design_flexural_reinforcement(self, mu: float, beam_geometry: BeamGeometry,
                                    material_props: MaterialProperties) -> ReinforcementDesign:
        """
        Design flexural reinforcement for rectangular or T-beam sections
        ACI 318M-25 Chapter 9
        
        Args:
            mu: Factored moment (kN⋅m)
            beam_geometry: Beam geometric properties
            material_props: Material properties
            
        Returns:
            Reinforcement design results
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        
        # Convert moment to N⋅mm
        Mu = mu * 1e6
        
        # Check if compression reinforcement is needed
        phi = self.phi_factors['flexure_tension_controlled']
        
        # Maximum moment capacity with tension reinforcement only
        rho_max = self.calculate_maximum_reinforcement_ratio(fc_prime, fy, beam_geometry)
        As_max = rho_max * b * d
        
        # Calculate moment capacity with maximum tension reinforcement
        a_max = As_max * fy / (0.85 * fc_prime * b)
        Mn_max = As_max * fy * (d - a_max / 2)
        phi_Mn_max = phi * Mn_max
        
        if Mu <= phi_Mn_max:
            # Tension reinforcement only
            return self._design_tension_reinforcement_only(Mu, beam_geometry, material_props)
        else:
            # Compression reinforcement required
            return self._design_doubly_reinforced_section(Mu, beam_geometry, material_props)
    
    def _design_tension_reinforcement_only(self, Mu: float, beam_geometry: BeamGeometry,
                                         material_props: MaterialProperties) -> ReinforcementDesign:
        """Design tension reinforcement only"""
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        
        phi = self.phi_factors['flexure_tension_controlled']
        
        # Corrected Quadratic equation coefficients
        A = phi * fy**2 / (2 * 0.85 * fc_prime * b)
        B = -phi * fy * d  # Must be negative
        C = Mu             # Must be positive
        
        # Solve quadratic equation (using the negative root for the physically valid tension-controlled state)
        discriminant = B**2 - 4*A*C
        if discriminant < 0:
            raise ValueError("Section inadequate for applied moment")
            
        As_required = (-B - math.sqrt(discriminant)) / (2*A)
        
        # Check minimum reinforcement
        rho_min = self.calculate_minimum_reinforcement_ratio(fc_prime, fy)
        As_min = rho_min * b * d
        As_required = max(As_required, As_min)
        
        # Select reinforcement bars considering spacing limits
        main_bars = self._select_reinforcement_bars(
            As_required, 
            beam_geometry, 
            fy, 
            stirrup_size='D10'
        )
        
        # Calculate development length
        main_bar_size = main_bars[0] if main_bars else 'D20'
        ld = self.aci.calculate_development_length(main_bar_size, fc_prime, fy)
        
        return ReinforcementDesign(
            main_bars=main_bars,
            main_area=As_required,
            compression_bars=[],
            compression_area=0.0,
            stirrups='D10',  
            stirrup_spacing=200.0,  
            development_length=ld
        )
    
    def _design_doubly_reinforced_section(self, Mu: float, beam_geometry: BeamGeometry,
                                        material_props: MaterialProperties) -> ReinforcementDesign:
        """Design doubly reinforced section with compression reinforcement"""
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        es = material_props.es
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        d_prime = beam_geometry.cover + 20  # Assume 20mm to center of compression bars
        
        phi = self.phi_factors['flexure_tension_controlled']
        
        # Maximum tension reinforcement without compression steel
        rho_max = self.calculate_maximum_reinforcement_ratio(fc_prime, fy, beam_geometry)
        As1 = rho_max * b * d
        
        # Moment capacity with As1 only
        a1 = As1 * fy / (0.85 * fc_prime * b)
        Mn1 = As1 * fy * (d - a1/2)
        
        # Additional moment requiring compression reinforcement
        Mu2 = Mu - phi * Mn1
        
        # Calculate actual stress in compression steel (fs')
        beta1 = self._calculate_beta1(fc_prime)
        c = a1 / beta1  # Depth to neutral axis
        
        # Strain in compression steel
        epsilon_s_prime = 0.003 * (c - d_prime) / c
        
        # Actual stress in compression steel (bounded by yield strength)
        fs_prime = max(0.0, min(epsilon_s_prime * es, fy))
        
        if fs_prime == 0.0:
            # If fs' is 0 or negative, the steel is at or below the neutral axis (in tension). 
            # The section dimensions are too small.
            raise ValueError("Compression steel is in the tension zone. Section must be resized.")
        
        # Design compression reinforcement using actual stress
        As2_prime = Mu2 / (phi * fs_prime * (d - d_prime))
        
        # Additional tension steel to balance compression steel
        As2 = As2_prime * (fs_prime / fy)  
        
        # Total tension reinforcement
        As_total = As1 + As2
        
        # Select reinforcement considering spacing limits
        main_bars = self._select_reinforcement_bars(
            As_total, 
            beam_geometry, 
            fy, 
            stirrup_size='D10'
        )
        comp_bars = self._select_reinforcement_bars(
            As2_prime, 
            beam_geometry, 
            fy, 
            stirrup_size='D10'
        )
        
        # Development length
        main_bar_size = main_bars[0] if main_bars else 'D25'
        ld = self.aci.calculate_development_length(main_bar_size, fc_prime, fy)
        
        return ReinforcementDesign(
            main_bars=main_bars,
            main_area=As_total,
            compression_bars=comp_bars,
            compression_area=As2_prime,
            stirrups='D10',
            stirrup_spacing=150.0,
            development_length=ld
        )
    
    def design_shear_reinforcement(self, vu: float, beam_geometry: BeamGeometry,
                                 material_props: MaterialProperties,
                                 main_reinforcement_area: float) -> Tuple[str, float]:
        """
        Design shear reinforcement (stirrups)
        ACI 318M-25 Chapter 22
        
        Args:
            vu: Factored shear force (kN)
            beam_geometry: Beam geometric properties
            material_props: Material properties
            main_reinforcement_area: Area of tension reinforcement (mm²)
            
        Returns:
            Tuple of (stirrup_size, spacing_mm)
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        
        # Convert shear to N
        Vu = vu * 1000
        
        # Concrete shear strength - ACI 318M-25 Section 22.5.5.1
        lambda_factor = 1.0  # Normal weight concrete
        Vc = lambda_factor * 0.17 * math.sqrt(fc_prime) * b * d  # N
        
        phi_v = self.phi_factors['shear']
        phi_Vc = phi_v * Vc
        
        # Check if shear reinforcement is required
        if Vu <= phi_Vc / 2:
            # No shear reinforcement required
            return 'None', 0.0
        elif Vu <= phi_Vc:
            # Minimum shear reinforcement required
            return self._design_minimum_stirrups(beam_geometry, material_props) # <-- Updated
        else:
            # Calculate required stirrup area
            Vs_required = Vu / phi_v - Vc  # Required shear from stirrups
            return self._design_stirrups_for_shear(Vs_required, beam_geometry, material_props) # <-- Updated
    
    def _design_minimum_stirrups(self, beam_geometry: BeamGeometry, material_props: MaterialProperties,
                                 vu: float = 0.0) -> Tuple[str, float]:
        """Design minimum stirrups - ACI 318M-25 Section 9.7.6.2.2"""
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        
        # Minimum stirrup area
        Av_min_1 = 0.062 * math.sqrt(fc_prime) * b / fy
        Av_min_2 = 0.35 * b / fy
        Av_min = max(Av_min_1, Av_min_2)
        
        # Select stirrup size and calculate spacing
        stirrup_size = 'D10'
        Av_stirrup = 2 * self.aci.get_bar_area(stirrup_size)  # Two legs
        s_max_calc = Av_stirrup / Av_min
        
        # Defensive high shear threshold check
        Vu = vu * 1000  # Convert to N
        phi_v = self.phi_factors['shear']
        Vc = 0.17 * math.sqrt(fc_prime) * b * d
        Vs_required = max(0.0, (Vu / phi_v) - Vc)
        Vs_threshold = 0.33 * math.sqrt(fc_prime) * b * d
        
        if Vs_required > Vs_threshold:
            s_max_limit = min(d / 4, 300.0)
        else:
            s_max_limit = min(d / 2, 600.0)
            
        s_actual = min(s_max_calc, s_max_limit)
        
        return stirrup_size, s_actual
    
    def _design_stirrups_for_shear(self, Vs_required: float, beam_geometry: BeamGeometry,
                                 material_props: MaterialProperties) -> Tuple[str, float]:
        """Design stirrups for required shear strength"""
        d = beam_geometry.effective_depth
        bw = beam_geometry.width
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        
        # Select stirrup size
        stirrup_size = 'D10'
        Av = 2 * self.aci.get_bar_area(stirrup_size)  # Two legs
        
        # Calculate required spacing: Vs = Av * fy * d / s
        s_required = Av * fy * d / Vs_required
        
        # Check high shear threshold: 0.33 * sqrt(fc') * bw * d
        Vs_threshold = 0.33 * math.sqrt(fc_prime) * bw * d
        
        # Maximum spacing limits - ACI 318M-25 Section 9.7.6.2.2
        if Vs_required > Vs_threshold:
            s_max = min(d / 4, 300.0)  # Halved limits for high shear
        else:
            s_max = min(d / 2, 600.0)  # Normal limits
            
        s_actual = min(s_required, s_max)
        
        # Check if larger stirrups are needed
        if s_actual < 75.0:  # Minimum practical spacing
            stirrup_size = 'D12'
            Av = 2 * self.aci.get_bar_area(stirrup_size)
            s_required_larger = Av * fy * d / Vs_required
            s_actual = min(s_required_larger, s_max)
        
        return stirrup_size, s_actual
    
    def _calculate_torsional_properties(self, beam_geometry: BeamGeometry, 
                                      stirrup_size: str = 'D10') -> Dict[str, float]:
        """
        Calculate cross-sectional properties for torsion
        ACI 318M-25 Chapter 22
        
        Args:
            beam_geometry: Beam geometric properties
            stirrup_size: Assumed closed stirrup size for Aoh calculation
            
        Returns:
            Dictionary containing Acp, pcp, Aoh, ph, and Ao
        """
        bw = beam_geometry.width
        h = beam_geometry.height
        cover = beam_geometry.cover
        db_stirrup = self.aci.get_bar_diameter(stirrup_size)
        
        # Gross section properties (Acp, pcp)
        Acp = bw * h
        pcp = 2 * (bw + h)
        
        # Properties of the area enclosed by the shear flow path (Aoh, ph)
        # Assuming clear cover to the outside of the stirrup
        x1 = bw - 2 * cover - db_stirrup
        y1 = h - 2 * cover - db_stirrup
        
        if x1 <= 0 or y1 <= 0:
            raise ValueError("Beam dimensions too small for the specified cover and stirrups.")
            
        Aoh = x1 * y1
        ph = 2 * (x1 + y1)
        
        # Gross area enclosed by shear flow path
        Ao = 0.85 * Aoh
        
        return {
            'Acp': Acp, 'pcp': pcp,
            'Aoh': Aoh, 'ph': ph,
            'Ao': Ao
        }

    def check_torsion_requirement(self, tu: float, beam_geometry: BeamGeometry, 
                                material_props: MaterialProperties) -> bool:
        """
        Check if torsion design is required (Tu > φTth)
        ACI 318M-25 Section 22.7.4
        
        Args:
            tu: Factored torsional moment (kN⋅m)
            beam_geometry: Beam geometric properties
            material_props: Material properties
            
        Returns:
            Boolean indicating if torsion reinforcement is required
        """
        if tu <= 0.0:
            return False
            
        fc_prime = material_props.fc_prime
        phi_t = self.phi_factors['torsion']
        props = self._calculate_torsional_properties(beam_geometry)
        
        # Threshold torsion (Tth) for non-prestressed members - ACI 318M-25 Eq. (22.7.4.1a)
        # Tth = 0.083 * λ * √fc' * (Acp² / pcp)
        lambda_factor = 1.0  # Normal weight concrete
        Tth = 0.083 * lambda_factor * math.sqrt(fc_prime) * (props['Acp']**2 / props['pcp']) / 1e6 # Convert to kN⋅m
        
        return tu > (phi_t * Tth)

    def design_combined_shear_torsion(self, vu: float, tu: float, beam_geometry: BeamGeometry,
                                    material_props: MaterialProperties) -> Tuple[str, float, float]:
        """
        Design transverse and longitudinal reinforcement for combined shear and torsion
        ACI 318M-25 Section 22.7
        """
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        fyt = material_props.fy # Transverse steel yield strength
        bw = beam_geometry.width
        d = beam_geometry.effective_depth
        
        props = self._calculate_torsional_properties(beam_geometry)
        phi_v = self.phi_factors['shear']
        phi_t = self.phi_factors['torsion']
        
        Vu = vu * 1000 # N
        Tu = tu * 1e6  # N⋅mm
        
        # 1. Concrete shear strength (Vc)
        lambda_factor = 1.0
        Vc = lambda_factor * 0.17 * math.sqrt(fc_prime) * bw * d # N
        
        # 2. Check cross-sectional adequacy (interaction limit) - ACI 318M-25 Section 22.7.7.1
        shear_stress = Vu / (bw * d)
        torsion_stress = (Tu * props['ph']) / (1.7 * props['Aoh']**2)
        combined_stress = math.sqrt(shear_stress**2 + torsion_stress**2)
        stress_limit = phi_v * ((Vc / (bw * d)) + 0.66 * math.sqrt(fc_prime))
        
        if combined_stress > stress_limit:
            raise ValueError(f"Cross-section inadequate for combined shear and torsion. Increase section dimensions. "
                             f"(Demand: {combined_stress:.2f} MPa, Limit: {stress_limit:.2f} MPa)")
                             
        # 3. Design Transverse Reinforcement (Stirrups)
        # Required shear reinforcement per mm (Av/s)
        Vs_required = max(0.0, (Vu / phi_v) - Vc)
        Av_over_s = Vs_required / (fyt * d) # mm²/mm (2 legs for standard shear)
        
        # Required torsion reinforcement per mm per leg (At/s) - ACI 318M-25 Eq. (22.7.6.1)
        theta = math.radians(45) # Typical assumption for non-prestressed
        At_over_s = Tu / (phi_t * 2 * props['Ao'] * fyt * (1 / math.tan(theta))) # mm²/mm (per leg)
        
        # Total transverse reinforcement per mm (A_{v+t}/s)
        required_transverse_per_mm = Av_over_s + 2 * At_over_s
        
        # Minimum transverse reinforcement - ACI 318M-25 Section 9.6.4.2
        min_transverse_1 = 0.062 * math.sqrt(fc_prime) * bw / fyt
        min_transverse_2 = 0.35 * bw / fyt
        min_transverse = max(min_transverse_1, min_transverse_2)
        
        design_transverse_per_mm = max(required_transverse_per_mm, min_transverse)
        
        # Select stirrup
        stirrup_size = 'D10'
        Av_stirrup = 2 * self.aci.get_bar_area(stirrup_size) # 2 legs of closed hoop
        s_calculated = Av_stirrup / design_transverse_per_mm
        
        # Spacing limits for torsion
        s_max_torsion = min(props['ph'] / 8, 300.0)
        
        # FIXED: Check high shear threshold for shear spacing limits
        Vs_threshold = 0.33 * math.sqrt(fc_prime) * bw * d
        if Vs_required > Vs_threshold:
            s_max_shear = min(d / 4, 300.0)  # Halved limits for high shear
        else:
            s_max_shear = min(d / 2, 600.0)  # Normal limits
            
        # Apply the most stringent spacing limit
        s_actual = min(s_calculated, s_max_torsion, s_max_shear)
        
        if s_actual < 75.0: # Minimum practical spacing
            stirrup_size = 'D12'
            Av_stirrup = 2 * self.aci.get_bar_area(stirrup_size)
            s_calculated = Av_stirrup / design_transverse_per_mm
            s_actual = min(s_calculated, s_max_torsion, s_max_shear)
            
        # 4. Design Longitudinal Torsion Reinforcement (Al) - ACI 318M-25 Section 22.7.6.1
        Al_required = At_over_s * props['ph'] * (fyt / fy) * (1 / math.tan(theta))**2
        
        # Minimum longitudinal reinforcement - ACI 318M-25 Section 9.6.4.3
        At_over_s_min = max(At_over_s, 0.175 * bw / fyt)
        Al_min = (0.42 * math.sqrt(fc_prime) * props['Acp'] / fy) - (At_over_s_min * props['ph'] * (fyt / fy))
        
        Al_design = max(Al_required, Al_min, 0.0)
        
        return stirrup_size, s_actual, Al_design
    
    def calculate_deflection(self, beam_geometry: BeamGeometry, material_props: MaterialProperties,
                           service_moment: float, reinforcement_area: float) -> float:
        """
        Calculate beam deflection - ACI 318M-25 Chapter 24
        
        Args:
            beam_geometry: Beam geometric properties
            material_props: Material properties
            service_moment: Service load moment (kN⋅m)
            reinforcement_area: Tension reinforcement area (mm²)
            
        Returns:
            Maximum deflection (mm)
        """
        # Simplified deflection calculation for uniformly loaded simply supported beam
        # More detailed analysis would require moment-curvature integration
        
        L = beam_geometry.length
        b = beam_geometry.width
        h = beam_geometry.height
        d = beam_geometry.effective_depth
        As = reinforcement_area
        
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        Ec = material_props.ec
        
        # Transform section properties
        n = 200000 / Ec  # Modular ratio
        rho = As / (b * d)
        
        # Neutral axis depth (cracked section)
        k = math.sqrt(2 * rho * n + (rho * n)**2) - rho * n
        
        # Moment of inertia (cracked section)
        Icr = (b * k**3 * d**3) / 3 + n * As * (d * (1 - k))**2
        
        # Effective moment of inertia - ACI 318M-25 Eq. (24.2.3.5)
        Ig = b * h**3 / 12  # Gross moment of inertia
        
        # Cracking moment
        fr = 0.62 * math.sqrt(fc_prime)  # Modulus of rupture
        yt = h / 2  # Distance to extreme tension fiber
        Mcr = fr * Ig / yt / 1e6  # Convert to kN⋅m
        
        # Effective moment of inertia
        if service_moment <= Mcr:
            Ie = Ig
        else:
            Ie = (Mcr / service_moment)**3 * Ig + (1 - (Mcr / service_moment)**3) * Icr
            Ie = max(Ie, Icr)
        
        # Deflection for simply supported beam with uniform load
        # Δ = 5ML²/(48EI) - simplified assumption
        deflection = (5 * service_moment * 1e6 * L**2) / (48 * Ec * Ie)
        
        return deflection
    
    def _select_reinforcement_bars(self, As_required: float, beam_geometry: BeamGeometry, 
                                   fy: float, stirrup_size: str = 'D10', aggregate_size: float = 25.0) -> List[str]:
        """
        Select reinforcement bars to provide required area while satisfying 
        ACI 318M-25 spacing limits (minimum clear spacing and maximum spacing for crack control).
        """
        # Available PNS 49 bar sizes and areas
        bar_data = [
            ('D16', 201.06), ('D20', 314.16), ('D25', 490.87), 
            ('D28', 615.75), ('D32', 804.25), ('D36', 1017.88), 
            ('D40', 1256.64), ('D50', 1963.50)
        ]
        
        # Calculate available width between stirrup legs
        d_stirrup = self.aci.get_bar_diameter(stirrup_size)
        cc = beam_geometry.cover  # Clear cover
        available_width = beam_geometry.width - (2 * cc) - (2 * d_stirrup)
        
        # Determine maximum spacing for crack control - ACI 318M-25 24.3.2
        crack_control_data = self.aci.check_crack_control(fy=fy, cc=cc)
        max_spacing = crack_control_data['max_spacing_mm']
        
        best_selection = []
        
        for bar_size, area in bar_data:
            num_bars = max(2, math.ceil(As_required / area)) 
            db = self.aci.get_bar_diameter(bar_size)
            
            # Minimum clear spacing - ACI 318M-25 Section 25.2.1
            min_clear_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
            
            # Required width for a single layer
            required_width = (num_bars * db) + ((num_bars - 1) * min_clear_spacing)
            
            # Calculate actual center-to-center spacing
            c2c_spacing = (available_width - db) / (num_bars - 1) if num_bars > 1 else 0.0
            
            # Check 1: Does it fit in a single layer?
            if required_width <= available_width:
                # Check 2: Does it violate max spacing for crack control?
                if c2c_spacing <= max_spacing:
                    return [bar_size] * num_bars
            else:
                # Fallback to 2 layers evaluation
                bars_per_layer = math.ceil(num_bars / 2)
                req_width_2_layers = (bars_per_layer * db) + ((bars_per_layer - 1) * min_clear_spacing)
                
                if req_width_2_layers <= available_width:
                    if not best_selection:
                        best_selection = [bar_size] * num_bars
        
        if best_selection:
            return best_selection
            
        # Fallback 2: Extremely narrow beam
        largest_bar, largest_area = bar_data[-1]
        num_largest = math.ceil(As_required / largest_area)
        return [largest_bar] * num_largest
    
    def _calculate_beta1(self, fc_prime: float) -> float:
        """Calculate β₁ factor for concrete - ACI 318M-25 Section 22.2.2.4.3"""
        if fc_prime <= 28.0:
            return 0.85
        elif fc_prime <= 55.0:
            return 0.85 - 0.05 * (fc_prime - 28.0) / 7.0
        else:
            return 0.65
    
    def perform_complete_beam_design(self, mu: float, vu: float, beam_geometry: BeamGeometry,
                                   material_props: MaterialProperties,
                                   service_moment: float = None,
                                   tu: float = 0.0) -> BeamAnalysisResult:
        """
        Perform complete beam design analysis including combined shear and torsion
        
        Args:
            mu: Factored moment (kN⋅m)
            vu: Factored shear (kN)
            beam_geometry: Beam geometric properties
            material_props: Material properties
            service_moment: Service moment for deflection (kN⋅m)
            tu: Factored torsional moment (kN⋅m) - Defaults to 0.0
            
        Returns:
            Complete beam analysis results
        """
        design_notes = []
        
        # 1. Flexural design (primary bending)
        flexural_design = self.design_flexural_reinforcement(mu, beam_geometry, material_props)
        
        # 2. Torsion and Shear Branching
        torsion_required = self.check_torsion_requirement(tu, beam_geometry, material_props)
        
        if torsion_required:
            stirrup_size, stirrup_spacing, al_required = self.design_combined_shear_torsion(
                vu, tu, beam_geometry, material_props
            )
            flexural_design.torsion_required = True
            flexural_design.torsion_longitudinal_area = al_required
            design_notes.append(f"Torsion design governed. Distribute {al_required:.1f} mm² of additional longitudinal steel around the section perimeter.")
        else:
            stirrup_size, stirrup_spacing = self.design_shear_reinforcement(
                vu, beam_geometry, material_props, flexural_design.main_area
            )
            flexural_design.torsion_required = False
            flexural_design.torsion_longitudinal_area = 0.0
            if tu > 0:
                design_notes.append("Torsion demand is below the threshold; combined shear-torsion design is not required.")
        
        flexural_design.stirrups = stirrup_size
        flexural_design.stirrup_spacing = stirrup_spacing
        
        # 3. Calculate capacities
        moment_capacity = self._calculate_moment_capacity(
            flexural_design.main_area, beam_geometry, material_props
        )
        
        shear_capacity = self._calculate_shear_capacity(
            beam_geometry, material_props, stirrup_size, stirrup_spacing
        )
        
        torsion_capacity = 0.0
        if torsion_required and stirrup_size != 'None':
            torsion_capacity = self._calculate_torsion_capacity(
                beam_geometry, material_props, stirrup_size, stirrup_spacing
            )
        
        # 4. Deflection calculation
        deflection = 0.0
        if service_moment:
            deflection = self.calculate_deflection(
                beam_geometry, material_props, service_moment, flexural_design.main_area
            )
        
        # 5. Utilization ratio
        # Retrieve strength reduction factors
        phi_m = self.phi_factors['flexure_tension_controlled'] 
        phi_v = self.phi_factors['shear']
        phi_t = self.phi_factors['torsion']
        
        # Calculate design capacities
        design_moment_cap = phi_m * moment_capacity
        design_shear_cap = phi_v * shear_capacity
        design_torsion_cap = phi_t * torsion_capacity
        
        utilization_moment = mu / design_moment_cap if design_moment_cap > 0 else 1.0
        utilization_shear = vu / design_shear_cap if design_shear_cap > 0 else 1.0
        utilization_torsion = tu / design_torsion_cap if design_torsion_cap > 0 else 0.0
        
        utilization_ratio = max(utilization_moment, utilization_shear, utilization_torsion)
        
        # 6. Standard design notes
        if flexural_design.compression_area > 0:
            design_notes.append("Compression reinforcement required")
        
        if stirrup_size == 'None':
            design_notes.append("No shear reinforcement required")
        
        if deflection > beam_geometry.length / 360:
            design_notes.append("Deflection may exceed typical limits")
        
        return BeamAnalysisResult(
            moment_capacity=moment_capacity,
            shear_capacity=shear_capacity,
            torsion_capacity=torsion_capacity,
            deflection=deflection,
            crack_width=0.0,
            reinforcement=flexural_design,
            utilization_ratio=utilization_ratio,
            design_notes=design_notes
        )
    
    def _calculate_moment_capacity(self, As: float, beam_geometry: BeamGeometry,
                                 material_props: MaterialProperties) -> float:
        """Calculate nominal moment capacity"""
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        
        # Calculate neutral axis depth
        a = As * fy / (0.85 * fc_prime * b)
        
        # Nominal moment capacity
        Mn = As * fy * (d - a/2) / 1e6  # Convert to kN⋅m
        
        return Mn
    
    def _calculate_shear_capacity(self, beam_geometry: BeamGeometry,
                                material_props: MaterialProperties,
                                stirrup_size: str, stirrup_spacing: float) -> float:
        """Calculate nominal shear capacity"""
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = beam_geometry.width
        d = beam_geometry.effective_depth
        
        # Concrete contribution
        Vc = 0.17 * math.sqrt(fc_prime) * b * d / 1000  # Convert to kN
        
        # Steel contribution
        if stirrup_size != 'None' and stirrup_spacing > 0:
            Av = 2 * self.aci.get_bar_area(stirrup_size)
            Vs = Av * fy * d / stirrup_spacing / 1000  # Convert to kN
        else:
            Vs = 0
        
        # Total shear capacity
        Vn = Vc + Vs
        
        return Vn
    
    def _calculate_torsion_capacity(self, beam_geometry: BeamGeometry,
                                  material_props: MaterialProperties,
                                  stirrup_size: str, stirrup_spacing: float) -> float:
        """Calculate nominal torsion capacity (Tn) based on provided stirrups"""
        if stirrup_size == 'None' or stirrup_spacing <= 0:
            return 0.0
            
        fyt = material_props.fy
        theta = math.radians(45) # Typical assumption for non-prestressed
        
        props = self._calculate_torsional_properties(beam_geometry, stirrup_size)
        At = self.aci.get_bar_area(stirrup_size) # Area of ONE leg
        
        # Nominal torsion capacity - ACI 318M-25 Eq. (22.7.6.1)
        # Tn = 2 * Ao * At * fyt * cot(θ) / s
        Tn = 2 * props['Ao'] * At * fyt * (1 / math.tan(theta)) / stirrup_spacing
        
        return Tn / 1e6 # Convert N⋅mm to kN⋅m