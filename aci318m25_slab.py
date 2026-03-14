# -*- coding: utf-8 -*-

"""
ACI 318M-25 Slab Design Library
Building Code Requirements for Structural Concrete - Slab Design

Based on:
- ACI CODE-318M-25 International System of Units
- Chapter 8: Two-Way Slab Systems
- Chapter 9: Flexural Design
- Chapter 24: Deflection Control

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.0
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties

class SlabType(Enum):
    """Types of slab systems"""
    ONE_WAY = "one_way"
    TWO_WAY_FLAT = "two_way_flat"
    TWO_WAY_BEAMS = "two_way_with_beams"
    FLAT_PLATE = "flat_plate"
    FLAT_SLAB = "flat_slab"
    WAFFLE_SLAB = "waffle_slab"

class SupportCondition(Enum):
    """Support conditions for slabs"""
    SIMPLY_SUPPORTED = "simply_supported"
    FIXED = "fixed"
    CONTINUOUS = "continuous"
    CANTILEVER = "cantilever"

class LoadPattern(Enum):
    """Load patterns for slab analysis"""
    UNIFORM = "uniform"
    POINT_LOAD = "point_load"
    LINE_LOAD = "line_load"
    PARTIAL_UNIFORM = "partial_uniform"

@dataclass
class SlabGeometry:
    """Slab geometry properties"""
    length_x: float           # Slab length in x-direction (mm)
    length_y: float           # Slab length in y-direction (mm)
    thickness: float          # Slab thickness (mm)
    cover: float              # Concrete cover (mm)
    effective_depth_x: float  # Effective depth for x-direction reinforcement (mm)
    effective_depth_y: float  # Effective depth for y-direction reinforcement (mm)
    slab_type: SlabType       # Type of slab system
    support_conditions: Dict[str, SupportCondition]  # Support conditions for each edge

@dataclass
class SlabLoads:
    """Slab loading conditions"""
    dead_load: float          # Dead load (kN/m²)
    live_load: float          # Live load (kN/m²)
    superimposed_dead: float  # Superimposed dead load (kN/m²)
    load_pattern: LoadPattern # Load distribution pattern
    load_factors: Dict[str, float]  # Load factors for combinations

@dataclass
class SlabReinforcement:
    """Slab reinforcement design"""
    main_bars_x: str          # Main reinforcement in x-direction
    main_spacing_x: float     # Spacing of x-direction bars (mm)
    main_bars_y: str          # Main reinforcement in y-direction
    main_spacing_y: float     # Spacing of y-direction bars (mm)
    shrinkage_bars: str       # Shrinkage and temperature reinforcement
    shrinkage_spacing: float  # Shrinkage reinforcement spacing (mm)
    top_bars: str             # Top reinforcement over supports
    top_spacing: float        # Top reinforcement spacing (mm)

@dataclass
class SlabMoments:
    """Slab moment results"""
    moment_x_positive: float  # Positive moment in x-direction (kN⋅m/m)
    moment_x_negative: float  # Negative moment in x-direction (kN⋅m/m)
    moment_y_positive: float  # Positive moment in y-direction (kN⋅m/m)
    moment_y_negative: float  # Negative moment in y-direction (kN⋅m/m)
    shear_x: float            # Shear in x-direction (kN/m)
    shear_y: float            # Shear in y-direction (kN/m)

@dataclass
class SlabAnalysisResult:
    """Complete slab analysis results"""
    moments: SlabMoments
    reinforcement: SlabReinforcement
    deflection: float         # Maximum deflection (mm)
    crack_width: float        # Maximum crack width (mm)
    punching_shear_ok: bool   # Punching shear check result
    utilization_ratio: float # Maximum utilization ratio
    design_notes: List[str]   # Design notes and warnings

class ACI318M25SlabDesign:
    """
    ACI 318M-25 Slab Design Library
    
    Comprehensive slab design according to ACI 318M-25:
    - One-way and two-way slab systems (Chapter 8)
    - Flexural design (Chapter 9)
    - Deflection control (Chapter 24)
    - Punching shear (Chapter 22)
    - Minimum reinforcement requirements
    """
    
    def __init__(self):
        """Initialize slab design calculator"""
        self.aci = ACI318M25()
        
        # Strength reduction factors φ - ACI 318M-25 Section 21.2
        self.phi_factors = {
            'flexure': 0.90,
            'shear': 0.75,
            'bearing': 0.65
        }
        
        # Minimum thickness requirements - ACI 318M-25 Table 7.3.1.1
        self.min_thickness_ratios = {
            SlabType.ONE_WAY: {
                SupportCondition.SIMPLY_SUPPORTED: 20,
                SupportCondition.FIXED: 28,
                SupportCondition.CONTINUOUS: 24,
                SupportCondition.CANTILEVER: 10
            },
            SlabType.TWO_WAY_FLAT: {
                SupportCondition.SIMPLY_SUPPORTED: 30,
                SupportCondition.FIXED: 36,
                SupportCondition.CONTINUOUS: 33
            }
        }
        
        # Deflection limits - ACI 318M-25 Table 24.2.2
        self.deflection_limits = {
            'immediate': {
                'flat_roof': 180,      # L/180
                'floor': 360,          # L/360
                'roof_floor': 240      # L/240
            },
            'long_term': {
                'supporting_nonstructural': 480,  # L/480
                'not_supporting': 240             # L/240
            }
        }
    
    def calculate_minimum_thickness(self, geometry: SlabGeometry, 
                                  material_props: MaterialProperties) -> float:
        """
        Calculate minimum slab thickness
        ACI 318M-25 Table 7.3.1.1 and Section 8.3.1
        
        Args:
            geometry: Slab geometric properties
            material_props: Material properties
            
        Returns:
            Minimum required thickness (mm)
        """
        # Get span ratios
        aspect_ratio = max(geometry.length_x, geometry.length_y) / min(geometry.length_x, geometry.length_y)
        longer_span = max(geometry.length_x, geometry.length_y)
        
        if geometry.slab_type == SlabType.ONE_WAY:
            # One-way slab thickness
            support_type = list(geometry.support_conditions.values())[0]
            ratio = self.min_thickness_ratios[SlabType.ONE_WAY][support_type]
            h_min = longer_span / ratio
            
        elif geometry.slab_type in [SlabType.TWO_WAY_FLAT, SlabType.FLAT_PLATE]:
            # Two-way slab without beams - ACI 318M-25 Section 8.3.1.1
            perimeter = 2 * (geometry.length_x + geometry.length_y)
            ln = longer_span - 200  # Assume 200mm support width
            
            # Basic minimum thickness
            h_min = ln * (0.8 + material_props.fy / 1400) / 36
            
            # Minimum absolute thickness
            h_min = max(h_min, 125)  # 125mm minimum for slabs without beams
            
        else:
            # Two-way slab with beams
            h_min = longer_span / 36  # Simplified approach
            h_min = max(h_min, 90)   # 90mm minimum for slabs with beams
        
        return h_min
    
    def calculate_slab_moments_one_way(self, geometry: SlabGeometry, 
                                     loads: SlabLoads) -> SlabMoments:
        """
        Calculate moments for one-way slabs
        ACI 318M-25 Chapter 7
        
        Args:
            geometry: Slab geometric properties
            loads: Loading conditions
            
        Returns:
            Slab moments
        """
        # Total factored load
        wu = (loads.dead_load + loads.superimposed_dead) * loads.load_factors.get('D', 1.4) + \
             loads.live_load * loads.load_factors.get('L', 1.6)
        
        # Convert span to meters for moment calculation
        span = max(geometry.length_x, geometry.length_y) / 1000  # Convert mm to m
        
        # Support conditions
        support_type = list(geometry.support_conditions.values())[0]
        
        if support_type == SupportCondition.SIMPLY_SUPPORTED:
            moment_positive = wu * span**2 / 8  # kN⋅m/m
            moment_negative = 0.0
        elif support_type == SupportCondition.FIXED:
            moment_positive = wu * span**2 / 24  # kN⋅m/m
            moment_negative = wu * span**2 / 12  # kN⋅m/m
        elif support_type == SupportCondition.CONTINUOUS:
            moment_positive = wu * span**2 / 16  # kN⋅m/m
            moment_negative = wu * span**2 / 12  # kN⋅m/m
        else:  # Cantilever
            moment_positive = 0.0
            moment_negative = wu * span**2 / 2  # kN⋅m/m
        
        return SlabMoments(
            moment_x_positive=moment_positive,
            moment_x_negative=moment_negative,
            moment_y_positive=0.0,  # No moment in y-direction for one-way
            moment_y_negative=0.0,
            shear_x=wu * span / 2,  # kN/m (wu in kN/m², span in m → kN/m)
            shear_y=0.0
        )
    
    def calculate_slab_moments_two_way(self, geometry: SlabGeometry,
                                     loads: SlabLoads) -> SlabMoments:
        """
        Calculate moments for two-way slabs using Direct Design Method approximations
        ACI 318M-25 Section 8.10
        
        Note: This calculates the governing (column strip) moments per meter width
        to ensure the most critical sections are safely reinforced.
        """
        # Total factored load (wu) in kN/m²
        wu = (loads.dead_load + loads.superimposed_dead) * loads.load_factors.get('D', 1.4) + \
             loads.live_load * loads.load_factors.get('L', 1.6)
        
        # Convert dimensions to meters
        lx = geometry.length_x / 1000
        ly = geometry.length_y / 1000
        
        # Assume standard 300mm column/support widths for clear span calculation (ln)
        # ACI 318 limits clear span to not less than 65% of center-to-center span
        ln_x = max(lx - 0.300, 0.65 * lx)
        ln_y = max(ly - 0.300, 0.65 * ly)
        
        # Total static moment in each direction (Mo) - ACI 318M-25 Eq. (8.10.3.2)
        # Mo = wu * l2 * ln^2 / 8
        Mo_x = wu * ly * (ln_x ** 2) / 8  # Design span is x, transverse width is y
        Mo_y = wu * lx * (ln_y ** 2) / 8  # Design span is y, transverse width is x
        
        # Distribution factors for interior vs exterior spans (Simplified)
        # If any support is simply supported, treat as an exterior panel without edge beams
        supports = list(geometry.support_conditions.values())
        if SupportCondition.SIMPLY_SUPPORTED in supports:
            # Exterior panel approximation
            neg_factor = 0.70  # Interior negative
            pos_factor = 0.52  # Positive
        else:
            # Interior panel - ACI 318M-25 Sec 8.10.4.1
            neg_factor = 0.65
            pos_factor = 0.35
            
        # Total positive and negative moments per panel
        M_neg_x_total = neg_factor * Mo_x
        M_pos_x_total = pos_factor * Mo_x
        
        M_neg_y_total = neg_factor * Mo_y
        M_pos_y_total = pos_factor * Mo_y
        
        # Convert to critical moments per meter width (Column Strip)
        # Column strip width is 0.5 * min(lx, ly) per ACI 318
        cs_width = 0.5 * min(lx, ly)
        
        # ACI 318 Sec 8.10.5: Column strips take ~75% of negative moment and ~60% of positive moment
        moment_x_negative = (0.75 * M_neg_x_total) / cs_width
        moment_x_positive = (0.60 * M_pos_x_total) / cs_width
        
        moment_y_negative = (0.75 * M_neg_y_total) / cs_width
        moment_y_positive = (0.60 * M_pos_y_total) / cs_width
        
        # Shear forces per meter width (governing edge)
        # Uses clear span for critical shear calculations
        shear_x = wu * ln_x / 2
        shear_y = wu * ln_y / 2
        
        return SlabMoments(
            moment_x_positive=moment_x_positive,
            moment_x_negative=moment_x_negative,
            moment_y_positive=moment_y_positive,
            moment_y_negative=moment_y_negative,
            shear_x=shear_x,
            shear_y=shear_y
        )
    
    def design_flexural_reinforcement(self, moment: float, width: float,
                                      effective_depth: float, thickness: float, cover: float,
                                      material_props: MaterialProperties) -> Tuple[str, float]:
        """Design flexural reinforcement for slab"""
        fc_prime = material_props.fc_prime
        fy = material_props.fy
        b = width
        d = effective_depth
        
        Mu = moment * 1e6
        
        if Mu <= 0:
            return self._design_minimum_reinforcement(b, thickness, fy, cover)
        
        phi = self.phi_factors['flexure']
        
        A = phi * fy**2 / (2 * 0.85 * fc_prime * b)
        B = -phi * fy * d  
        C = Mu             
        
        discriminant = B**2 - 4*A*C
        if discriminant < 0:
            raise ValueError("Section inadequate for applied moment")
        
        As_required = (-B - math.sqrt(discriminant)) / (2*A)
        
        # Updated call to pass 'thickness' instead of 'effective_depth'
        As_min = self._calculate_minimum_slab_reinforcement(b, thickness, fy)
        As_required = max(As_required, As_min)
        
        As_max = 0.025 * b * d
        if As_required > As_max:
            raise ValueError("Required reinforcement exceeds practical maximum")
        
        return self._select_slab_reinforcement(As_required, b, fy, thickness, cover)
    
    def _design_minimum_reinforcement(self, width: float, thickness: float,
                                      fy: float, cover: float) -> Tuple[str, float]:
        """Design minimum reinforcement for slabs"""
        if fy <= 420:
            rho_min = 0.0020
        elif fy <= 520:
            rho_min = 0.0018
        else:
            rho_min = 0.0018 * 420 / fy
        
        As_min = rho_min * width * thickness
        return self._select_slab_reinforcement(As_min, width, fy, thickness, cover)
    
    def _calculate_minimum_slab_reinforcement(self, width: float, 
                                            thickness: float,
                                            fy: float) -> float:
        """Calculate minimum flexural reinforcement for slabs (shrinkage and temperature limit)"""
        # Minimum shrinkage and temperature reinforcement per ACI 318M-25 Section 24.4
        if fy <= 420:
            rho_temp = 0.0020
        elif fy <= 520:
            rho_temp = 0.0018
        else:
            rho_temp = 0.0018 * 420.0 / fy
        
        # For slabs, minimum flexural reinforcement is governed by gross area
        As_min_temp = rho_temp * width * thickness
        
        return As_min_temp
    
    def _select_slab_reinforcement(self, As_required: float, width: float,
                                   fy: float, thickness: float, cover: float,
                                   aggregate_size: float = 25.0) -> Tuple[str, float]:
        """Select appropriate bar size and spacing for slab considering ACI 318M-25 limits"""
        # Common slab bar sizes
        bar_sizes = ['D10', 'D12', 'D16', 'D20']
        
        # Calculate maximum spacing for crack control (ACI 318M-25 Sec. 24.3.2)
        fs = (2.0 / 3.0) * fy
        s_limit_1 = 380 * (280 / fs) - 2.5 * cover
        s_limit_2 = 300 * (280 / fs)
        max_crack_spacing = min(s_limit_1, s_limit_2)
        
        # General slab maximum spacing limit (ACI 318M-25 Sec. 7.7.2.3 / 8.7.2.2)
        max_general_spacing = min(3 * thickness, 450.0)
        
        # Governing maximum spacing
        max_spacing = min(max_crack_spacing, max_general_spacing)
        
        for bar_size in bar_sizes:
            bar_area = self.aci.get_bar_area(bar_size)
            db = self.aci.get_bar_diameter(bar_size)
            
            # Theoretical required spacing to meet area
            spacing = bar_area * width / As_required
            
            # Minimum clear spacing (ACI 318M-25 Sec. 25.2.1)
            min_clear_spacing = max(25.0, db, (4.0/3.0) * aggregate_size)
            min_c2c_spacing = min_clear_spacing + db
            
            if min_c2c_spacing <= spacing <= max_spacing:
                return bar_size, spacing
        
        # If no suitable single size fits perfectly, use smallest bar with maximum allowable spacing
        bar_size = 'D10'
        bar_area = self.aci.get_bar_area(bar_size)
        spacing = min(max_spacing, bar_area * width / As_required)
        
        return bar_size, spacing
    
    def check_punching_shear(self, geometry: SlabGeometry,
                           material_props: MaterialProperties,
                           column_dimensions: Tuple[float, float],
                           punching_force: float) -> Tuple[bool, float]:
        """Check punching shear around columns - ACI 318M-25 Section 22.6"""
        fc_prime = material_props.fc_prime
        d = min(geometry.effective_depth_x, geometry.effective_depth_y)
        
        col_width, col_depth = column_dimensions
        
        # Calculate true beta for rectangular columns
        col_max = max(col_width, col_depth)
        col_min = min(col_width, col_depth)
        beta = col_max / col_min if col_min > 0 else 1.0
        
        bo = 2 * (col_width + d) + 2 * (col_depth + d)
        
        # Equation 1: Basic punching shear (Now using true beta)
        vc1 = 0.17 * (1 + 2/beta) * math.sqrt(fc_prime)
        
        # Equation 2: Based on column location (Assuming interior alphas = 40)
        alphas = 40  
        vc2 = 0.083 * (alphas * d / bo + 2) * math.sqrt(fc_prime)
        
        # Equation 3: Maximum punching shear
        vc3 = 0.33 * math.sqrt(fc_prime)
        
        vc = min(vc1, vc2, vc3)
        Vn = vc * bo * d / 1000  # Convert to kN
        
        phi = self.phi_factors['shear']
        phi_Vn = phi * Vn
        
        is_adequate = punching_force <= phi_Vn
        utilization_ratio = punching_force / phi_Vn if phi_Vn > 0 else float('inf')
        
        return is_adequate, utilization_ratio
    
    def calculate_deflection(self, geometry: SlabGeometry,
                           material_props: MaterialProperties,
                           service_loads: SlabLoads,
                           reinforcement_x: float,
                           reinforcement_y: float) -> float:
        """Calculate slab deflection - ACI 318M-25 Chapter 24"""
        w_service = service_loads.dead_load + service_loads.superimposed_dead + service_loads.live_load
        
        # Convert load from kN/m² to N/mm for a 1000mm strip width
        w_service_n_mm = w_service / 1000.0  
        
        Ec = material_props.ec
        fc_prime = material_props.fc_prime
        h = geometry.thickness
        lx_mm = min(geometry.length_x, geometry.length_y)
        lx_m = lx_mm / 1000.0
        
        # Enforce consistent 1000 mm strip width
        b = 1000.0
        Ig = (b * h**3) / 12.0
        fr = 0.62 * math.sqrt(fc_prime)
        
        # Cracking moment in N⋅mm
        Mcr_n_mm = fr * Ig / (h / 2.0) 
        
        # Service moment calculation (yields kN⋅m, convert to N⋅mm)
        if geometry.slab_type == SlabType.ONE_WAY:
            M_service_kn_m = w_service * (lx_m**2) / 8.0
        else:
            M_service_kn_m = w_service * (lx_m**2) / 16.0
            
        M_service_n_mm = M_service_kn_m * 1e6
        
        n = 200000.0 / Ec
        As = max(reinforcement_x, reinforcement_y)
        d = geometry.effective_depth_x
        rho = As / (b * d)
        
        k = math.sqrt(2 * rho * n + (rho * n)**2) - rho * n
        Icr = (b * k**3 * d**3) / 3.0 + n * As * (d * (1.0 - k))**2
        
        if M_service_n_mm <= Mcr_n_mm:
            Ie = Ig
        else:
            Ie = (Mcr_n_mm / M_service_n_mm)**3 * Ig + (1.0 - (Mcr_n_mm / M_service_n_mm)**3) * Icr
            Ie = max(Ie, Icr)
        
        # Deflection using consistent N, mm, MPa units
        if geometry.slab_type == SlabType.ONE_WAY:
            deflection = 5.0 * w_service_n_mm * (lx_mm**4) / (384.0 * Ec * Ie)
        else:
            alpha = 0.001 
            deflection = alpha * w_service_n_mm * (lx_mm**4) / (Ec * Ie)
        
        return deflection
    
    def perform_complete_slab_design(self, geometry: SlabGeometry,
                                   loads: SlabLoads,
                                   material_props: MaterialProperties,
                                   column_size: Tuple[float, float] = None) -> SlabAnalysisResult:
        """
        Perform complete slab design analysis
        
        Args:
            geometry: Slab geometric properties
            loads: Loading conditions
            material_props: Material properties
            column_size: Column dimensions for punching shear check
            
        Returns:
            Complete slab analysis results
        """
        design_notes = []
        
        # Check minimum thickness
        h_min = self.calculate_minimum_thickness(geometry, material_props)
        if geometry.thickness < h_min:
            design_notes.append(f"Increase thickness to minimum {h_min:.0f}mm")
        
        # Calculate moments
        if geometry.slab_type == SlabType.ONE_WAY:
            moments = self.calculate_slab_moments_one_way(geometry, loads)
        else:
            moments = self.calculate_slab_moments_two_way(geometry, loads)
        
        # Design reinforcement
        bar_x, spacing_x = self.design_flexural_reinforcement(
            moments.moment_x_positive, 1000, geometry.effective_depth_x, geometry.thickness, geometry.cover, material_props
        )
        
        bar_y, spacing_y = self.design_flexural_reinforcement(
            moments.moment_y_positive, 1000, geometry.effective_depth_y, geometry.thickness, geometry.cover, material_props
        )
        
        # Top reinforcement for negative moments
        if moments.moment_x_negative > 0:
            bar_top, spacing_top = self.design_flexural_reinforcement(
                moments.moment_x_negative, 1000, geometry.effective_depth_x, geometry.thickness, geometry.cover, material_props
            )
        else:
            bar_top, spacing_top = self._design_minimum_reinforcement(
                1000, geometry.thickness, material_props.fy, geometry.cover
            )
        
        # Shrinkage and temperature reinforcement
        bar_shrink, spacing_shrink = self._design_minimum_reinforcement(
            1000, geometry.thickness, material_props.fy, geometry.cover
        )
        
        # Calculate reinforcement areas
        As_x = self.aci.get_bar_area(bar_x) * 1000 / spacing_x
        As_y = self.aci.get_bar_area(bar_y) * 1000 / spacing_y
        
        # Deflection calculation
        service_loads = SlabLoads(
            dead_load=loads.dead_load,
            live_load=loads.live_load,
            superimposed_dead=loads.superimposed_dead,
            load_pattern=loads.load_pattern,
            load_factors={'D': 1.0, 'L': 1.0}  # Service load factors
        )
        
        deflection = self.calculate_deflection(
            geometry, material_props, service_loads, As_x, As_y
        )
        
        # Check deflection limits
        span = max(geometry.length_x, geometry.length_y)
        deflection_limit = span / self.deflection_limits['immediate']['floor']
        
        if deflection > deflection_limit:
            design_notes.append(f"Deflection {deflection:.1f}mm exceeds limit {deflection_limit:.1f}mm")
        
        # Punching shear check
        punching_shear_ok = True
        if column_size and geometry.slab_type in [SlabType.FLAT_PLATE, SlabType.FLAT_SLAB]:
            punching_force = (loads.dead_load + loads.live_load) * \
                           geometry.length_x * geometry.length_y / 1000  # Approximate
            punching_shear_ok, punch_ratio = self.check_punching_shear(
                geometry, material_props, column_size, punching_force
            )
            if not punching_shear_ok:
                design_notes.append("Punching shear inadequate - increase slab thickness or add shear reinforcement")
        
        # Calculate utilization ratios
        moment_utilization = max(
            moments.moment_x_positive / (As_x * material_props.fy * geometry.effective_depth_x * 0.9 / 1e6),
            moments.moment_y_positive / (As_y * material_props.fy * geometry.effective_depth_y * 0.9 / 1e6)
        ) if As_x > 0 and As_y > 0 else 0
        
        # FIXED: Actually incorporate punching shear into the utilization and remove the 1.0 clamp!
        punch_utilization = punch_ratio if 'punch_ratio' in locals() else 0.0
        utilization_ratio = max(moment_utilization, punch_utilization)
        
        # Create result objects
        reinforcement = SlabReinforcement(
            main_bars_x=bar_x,
            main_spacing_x=spacing_x,
            main_bars_y=bar_y,
            main_spacing_y=spacing_y,
            shrinkage_bars=bar_shrink,
            shrinkage_spacing=spacing_shrink,
            top_bars=bar_top,
            top_spacing=spacing_top
        )
        
        return SlabAnalysisResult(
            moments=moments,
            reinforcement=reinforcement,
            deflection=deflection,
            crack_width=0.0,  # Simplified - detailed crack analysis needed
            punching_shear_ok=punching_shear_ok,
            utilization_ratio=utilization_ratio,
            design_notes=design_notes
        )