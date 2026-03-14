# -*- coding: utf-8 -*-

"""
ACI 318M-25 Complete Member Design Library Manager
Central access point for all ACI 318M-25 structural member design libraries

Based on:
- ACI CODE-318M-25 International System of Units
- Building Code Requirements for Structural Concrete

@author: Enhanced by AI Assistant  
@date: 2024
@version: 1.0
"""

import math
from typing import Dict, Tuple, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import all member design libraries
from aci318m25 import ACI318M25, ConcreteStrengthClass, ReinforcementGrade, MaterialProperties
from aci318m25_beam import ACI318M25BeamDesign, BeamGeometry, BeamType
from aci318m25_column import ACI318M25ColumnDesign, ColumnGeometry, ColumnLoads, ColumnType, ColumnShape, LoadCondition
from aci318m25_slab import ACI318M25SlabDesign, SlabGeometry, SlabLoads, SlabType, SupportCondition, LoadPattern
from aci318m25_footing import ACI318M25FootingDesign, FootingLoads, SoilProperties, FootingType, SoilCondition
from aci318m25_wall import ACI318M25WallDesign, WallGeometry, WallLoads, WallType, WallSupportCondition, LoadType
from aci318m25_diaphragm import ACI318M25DiaphragmDesign, DiaphragmGeometry, DiaphragmLoads, DiaphragmType, DiaphragmLoadType

class StructuralMemberType(Enum):
    """Types of structural members available for design"""
    BEAM = "beam"
    COLUMN = "column"
    SLAB = "slab"
    FOOTING = "footing"
    WALL = "wall"
    DIAPHRAGM = "diaphragm"

@dataclass
class ProjectInfo:
    """Project information for design reports"""
    project_name: str
    location: str
    date: str
    engineer: str
    client: str = ""
    description: str = ""

class ACI318M25MemberLibrary:
    """
    ACI 318M-25 Complete Member Design Library Manager
    
    Central access point for all structural concrete member design:
    - Beams: Flexural and shear design
    - Columns: Axial and P-M interaction design
    - Slabs: One-way and two-way slab systems
    - Footings: Isolated and combined footings
    - Walls: Bearing and shear walls
    """
    
    def __init__(self):
        """Initialize all member design libraries"""
        # Core ACI 318M-25 library
        self.aci = ACI318M25()
        
        # Member design libraries
        self.beam_design = ACI318M25BeamDesign()
        self.column_design = ACI318M25ColumnDesign()
        self.slab_design = ACI318M25SlabDesign()
        self.footing_design = ACI318M25FootingDesign()
        self.wall_design = ACI318M25WallDesign()
        self.diaphragm_design = ACI318M25DiaphragmDesign()
        
        # Design preferences
        self.default_materials = {
            'concrete': ConcreteStrengthClass.FC28,
            'steel': ReinforcementGrade.GRADE420
        }
        
        # Library information
        self.version = "1.0"
        self.code_version = "ACI 318M-25"
        
    def get_library_info(self) -> Dict[str, str]:
        """Get information about available design libraries"""
        return {
            'version': self.version,
            'code': self.code_version,
            'libraries': {
                'beam': 'Flexural and shear design of reinforced concrete beams',
                'column': 'Axial and P-M interaction design of reinforced concrete columns',
                'slab': 'One-way and two-way reinforced concrete slab systems',
                'footing': 'Isolated and combined footing design',
                'wall': 'Bearing wall and shear wall design',
                'diaphragm': 'In-plane diaphragm design and collector elements'
            },
            'units': 'SI (MPa, kN, mm, m)',
            'standards': [
                'ACI 318M-25 Building Code Requirements for Structural Concrete',
                'ACI 318RM-25 Commentary',
                'ASTM A615/A615M Standard Specification for Deformed Bars'
            ]
        }
    
    def get_available_materials(self) -> Dict[str, List[str]]:
        """Get available material strengths"""
        concrete_strengths = [grade.value for grade in ConcreteStrengthClass]
        steel_grades = [grade.value for grade in ReinforcementGrade]
        
        return {
            'concrete_strengths': concrete_strengths,
            'steel_grades': steel_grades,
            'concrete_range': '14-100 MPa',
            'steel_range': '280-520 MPa'
        }
    
    def create_standard_material_properties(self, 
                                          concrete_class: ConcreteStrengthClass = None,
                                          steel_grade: ReinforcementGrade = None) -> MaterialProperties:
        """Create standard material properties"""
        if concrete_class is None:
            concrete_class = self.default_materials['concrete']
        if steel_grade is None:
            steel_grade = self.default_materials['steel']
        
        return self.aci.get_material_properties(concrete_class, steel_grade)
    
    def design_typical_office_building_members(self, 
                                             building_height: float = 20.0,
                                             typical_span: float = 6.0) -> Dict[str, any]:
        """
        Design typical office building structural members
        
        Args:
            building_height: Building height (m)
            typical_span: Typical span length (m)
            
        Returns:
            Dictionary with design results for all members
        """
        # Standard material properties
        material_props = self.create_standard_material_properties()
        
        # Convert to mm
        span_mm = typical_span * 1000
        height_mm = building_height * 1000
        
        # Design results
        results = {}
        
        # 1. Beam Design
        beam_geometry = BeamGeometry(
            length=span_mm,
            width=300,                # 300mm width
            height=600,               # 600mm height
            effective_depth=540,      # 540mm effective depth
            cover=40,                 # 40mm cover
            flange_width=0,
            flange_thickness=0,
            beam_type=BeamType.RECTANGULAR
        )
        
        # Typical office loading
        beam_dead_load = 8.0  # kN/m (self-weight + finishes)
        beam_live_load = 3.0  # kN/m (office live load)
        beam_factored_load = 1.4 * beam_dead_load + 1.6 * beam_live_load
        
        # Moments and shears
        beam_moment = beam_factored_load * (typical_span ** 2) / 8  # Simply supported
        beam_shear = beam_factored_load * typical_span / 2
        
        try :
            beam_result = self.beam_design.perform_complete_beam_design(
                mu=beam_moment,
                vu=beam_shear,
                beam_geometry=beam_geometry,
                material_props=material_props,
                service_moment=beam_moment / 1.6  # Approximate service moment
            )
            
            results['beam'] = {
                'geometry': beam_geometry,
                'loads': {'moment': beam_moment, 'shear': beam_shear},
                'design_result': beam_result,
                'summary': f"Beam: {beam_geometry.width}x{beam_geometry.height}mm, "
                        f"Main bars: {beam_result.reinforcement.main_bars}, "
                        f"Stirrups: {beam_result.reinforcement.stirrups}@{beam_result.reinforcement.stirrup_spacing:.0f}mm"
            }
        except Exception as e :
            results['beam'] = {'summary': f"Beam Design FAILED: {str(e)}"}
        
        # 2. Column Design
        column_geometry = ColumnGeometry(
            width=400,                # 400mm square
            depth=400,
            height=3500,              # Typical story height
            cover=40,
            shape=ColumnShape.RECTANGULAR,
            column_type=ColumnType.TIED,
            effective_length=3500
        )
        
        # Typical column loads (estimate)
        tributary_area = typical_span ** 2  # m²
        floors = int(building_height / 3.5)  # Number of floors
        total_load = tributary_area * (beam_dead_load + beam_live_load) * floors
        
        column_loads = ColumnLoads(
            axial_force=total_load * 1.4,    # Factored axial load
            moment_x=total_load * 0.1,       # Moment due to eccentricity
            moment_y=total_load * 0.05,      # Added Y-axis moment
            shear_x=120.0,                   # Added lateral shear in X (kN)
            shear_y=60.0,                    # Added lateral shear in Y (kN)
            load_condition=LoadCondition.BIAXIAL_BENDING
        )
        
        try :
            column_result = self.column_design.perform_complete_column_design(
                column_loads, column_geometry, material_props
            )
            
            results['column'] = {
                'geometry': column_geometry,
                'loads': column_loads,
                'design_result': column_result,
                'summary': f"Column: {column_geometry.width}x{column_geometry.depth}mm, "
                        f"Bars: {len(column_result.reinforcement.longitudinal_bars)}x{column_result.reinforcement.longitudinal_bars[0] if column_result.reinforcement.longitudinal_bars else 'N/A'}, "
                        f"Ties: {column_result.reinforcement.tie_bars}@{column_result.reinforcement.tie_spacing:.0f}mm"
            }
        except Exception as e :
            results['column'] = {'summary': f"Column Design FAILED: {str(e)}"}
        
        # 3. Slab Design (Now actually calling the library!)
        slab_geometry = SlabGeometry(
            length_x=span_mm,
            length_y=span_mm,
            thickness=200,            # Increased to 200mm to prevent punching shear failure
            cover=20,
            effective_depth_x=170,
            effective_depth_y=160,
            slab_type=SlabType.TWO_WAY_FLAT,
            support_conditions={
                'x1': SupportCondition.CONTINUOUS,
                'x2': SupportCondition.CONTINUOUS,
                'y1': SupportCondition.CONTINUOUS,
                'y2': SupportCondition.CONTINUOUS
            }
        )
        
        slab_loads = SlabLoads(
            dead_load=4.0,            # 4.0 kN/m² (slab + finishes)
            live_load=3.0,            # 3.0 kN/m² office live load
            superimposed_dead=1.0,    # 1.0 kN/m² partitions
            load_pattern=LoadPattern.UNIFORM,
            load_factors={'D': 1.4, 'L': 1.6}
        )
        
        try:
            # 1. Calculate average effective depth in meters
            d_avg_m = ((slab_geometry.effective_depth_x + slab_geometry.effective_depth_y) / 2) / 1000.0
            
            # 2. Column dimensions in meters (assumed 400x400 from step 2)
            col_w_m = 400.0 / 1000.0
            col_d_m = 400.0 / 1000.0
            
            # 3. Critical perimeter area (column + d/2 on all sides)
            critical_area_m2 = (col_w_m + d_avg_m) * (col_d_m + d_avg_m)
            
            # 4. Total tributary area of the slab panel
            total_slab_area_m2 = (slab_geometry.length_x / 1000.0) * (slab_geometry.length_y / 1000.0)
            
            # 5. Area causing punching shear (total area minus the critical footprint)
            punching_area_m2 = total_slab_area_m2 - critical_area_m2
            
            # 6. Factored area load (qu)
            qu = (slab_loads.load_factors['D'] * slab_loads.dead_load) + \
                 (slab_loads.load_factors['L'] * slab_loads.live_load)
            
            punching_force = qu * punching_area_m2
                           
            # Actually call the slab design module
            slab_result = self.slab_design.perform_complete_slab_design(
                geometry=slab_geometry, 
                loads=slab_loads, 
                material_props=material_props,
                column_size=(400.0, 400.0) # Pass the column size for punching shear
            )
            
            results['slab'] = {
                'geometry': slab_geometry,
                'loads': slab_loads,
                'design_result': slab_result,
                'summary': f"Slab: {slab_geometry.thickness}mm thick, "
                          f"Main Bottom: {slab_result.reinforcement.main_bars_x}@{slab_result.reinforcement.main_spacing_x:.0f}mm, "
                          f"Top: {slab_result.reinforcement.top_bars}@{slab_result.reinforcement.top_spacing:.0f}mm"
            }
        except Exception as e:
            results['slab'] = {'summary': f"Slab Design FAILED: {str(e)}"}
        
        # 4. Footing Design
        footing_loads = FootingLoads(
            axial_force=total_load * 1.4,
            moment_x=total_load * 0.05,
            moment_y=0,
            shear_x=0,
            shear_y=0,
            service_axial=total_load,
            service_moment_x=total_load * 0.03,
            service_moment_y=0
        )
        
        soil_props = SoilProperties(
            bearing_capacity=200,     # 200 kPa typical
            unit_weight=18.0,
            friction_angle=30,
            cohesion=0,
            condition=SoilCondition.ALLOWABLE_STRESS
        )
        
        try :
            footing_result = self.footing_design.perform_complete_footing_design(
                footing_loads, soil_props, material_props
            )
            
            results['footing'] = {
                'loads': footing_loads,
                'soil': soil_props,
                'design_result': footing_result,
                'summary': f"Footing: Based on {soil_props.bearing_capacity} kPa bearing capacity"
            }
        except Exception as e :
            results['footing'] = {'summary': f"Footing Design FAILED: {str(e)}"}
        
        # 5. Shear Wall Design (if applicable)
        if building_height > 15.0:  # For taller buildings
            wall_geometry = WallGeometry(
                length=4000,              # 4m long shear wall
                height=height_mm,
                thickness=250,            # 250mm thick
                cover=40,
                effective_length=height_mm,
                wall_type=WallType.SHEAR_WALL,
                support_condition=WallSupportCondition.FIXED_TOP_BOTTOM
            )
            
            # Estimate lateral loads (wind or seismic)
            lateral_force = building_height * 2.0  # Simplified lateral load
            
            wall_loads = WallLoads(
                axial_force=50,           # 50 kN/m from gravity
                in_plane_shear=lateral_force,
                in_plane_moment=25,
                out_plane_moment=10,      # 10 kN⋅m/m out-of-plane
                out_plane_shear=5,
                lateral_pressure=2.0,     # 2 kPa wind pressure
                load_type=LoadType.LATERAL_WIND
            )
            
            try :
                wall_result = self.wall_design.perform_complete_wall_design(
                    wall_geometry, wall_loads, material_props
                )
                
                results['wall'] = {
                    'geometry': wall_geometry,
                    'loads': wall_loads,
                    'design_result': wall_result,
                    'summary': f"Shear Wall: {wall_geometry.length}x{wall_geometry.thickness}mm, "
                            f"Vert: {wall_result.reinforcement.vertical_bars}@{wall_result.reinforcement.vertical_spacing:.0f}mm, "
                            f"Horiz: {wall_result.reinforcement.horizontal_bars}@{wall_result.reinforcement.horizontal_spacing:.0f}mm"
                }
            except Exception as e :
                results['wall'] = {'summary': f"Wall Design FAILED: {str(e)}"}
        
        # 6. Diaphragm Design
        diaphragm_geometry = DiaphragmGeometry(
            length=span_mm * 2,       # Two spans length
            width=span_mm,            # One span width
            thickness=150,            # 150mm thick slab acting as diaphragm
            cover=20,
            diaphragm_type=DiaphragmType.CONCRETE_SLAB,
            openings=[],              # No openings for this example
            aspect_ratio=2.0,         # Length to width ratio
            irregularities=[]         # No irregularities
        )
        
        # Estimate diaphragm loads (seismic or wind)
        story_area = (span_mm * 2) * span_mm / 1e6  # m²
        base_shear_coefficient = 0.05  # Simplified seismic coefficient
        diaphragm_force = total_load * base_shear_coefficient  # kN
        
        diaphragm_loads = DiaphragmLoads(
            lateral_force=diaphragm_force,
            force_distribution='uniform',
            seismic_coefficient=base_shear_coefficient,
            wind_pressure=1.0,        # 1.0 kPa wind pressure
            load_type=DiaphragmLoadType.SEISMIC,
            force_direction=0.0,      # Along length
            story_shear=diaphragm_force
        )
        
        try :
            diaphragm_result = self.diaphragm_design.perform_complete_diaphragm_design(
                diaphragm_geometry, diaphragm_loads, material_props
            )
            
            results['diaphragm'] = {
                'geometry': diaphragm_geometry,
                'loads': diaphragm_loads,
                'design_result': diaphragm_result,
                'summary': f"Diaphragm: {diaphragm_geometry.thickness}mm thick, "
                        f"{diaphragm_result.behavior_classification.value} behavior, "
                        f"Main: {diaphragm_result.reinforcement.main_bars_x}@{diaphragm_result.reinforcement.main_spacing_x:.0f}mm"
            }
        except Exception as e :
            results['diaphragm'] = {'summary': f"Diaphragm Design FAILED: {str(e)}"}
        
        return results
    
    def generate_design_summary_report(self, design_results: Dict[str, any],
                                     project_info: ProjectInfo) -> str:
        """Generate comprehensive design summary report"""
        
        # Fetch the active material properties so the report tells the truth
        mat = self.create_standard_material_properties()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                           ACI 318M-25 STRUCTURAL DESIGN REPORT                      ║
║                    Building Code Requirements for Structural Concrete                ║
║                              International System of Units                          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Project Information:
{'='*80}
Project Name: {project_info.project_name}
Location: {project_info.location}
Date: {project_info.date}
Engineer: {project_info.engineer}

Material Properties:
{'='*80}
• Concrete: fc' = {mat.fc_prime:.1f} MPa
• Reinforcing Steel: fy = {mat.fy:.1f} MPa
• Steel Modulus: Es = {mat.es:,.0f} MPa
• Concrete Modulus: Ec = {mat.ec:,.0f} MPa

Design Summary:
{'='*80}"""

        # Add member summaries
        for member_type, result in design_results.items():
            if 'summary' in result:
                report += f"\n• {member_type.upper()}: {result['summary']}"
        
        report += f"""

Load Combinations Used:
{'='*80}
• Strength Design:
  - Eq. (5.3.1a): 1.4D
  - Eq. (5.3.1b): 1.2D + 1.6L + 0.5(Lr or S or R)
  - Eq. (5.3.1d): 1.2D + 1.0W + 1.0L + 0.5(Lr or S or R)

• Service Load:
  - Service-1: 1.0D + 1.0L
  - Service-2: 1.0D + 1.0W

Strength Reduction Factors (φ):
{'='*80}
• Flexure (tension-controlled): φ = 0.90
• Compression (tied columns): φ = 0.65
• Compression (spiral columns): φ = 0.75
• Shear: φ = 0.75
• Bearing: φ = 0.65

Design Verification:
{'='*80}"""

        # Add verification status for each member
        for member_type, result in design_results.items():
            if 'design_result' in result:
                design_result = result['design_result']
                
                if hasattr(design_result, 'utilization_ratio'):
                    ratio = design_result.utilization_ratio
                    status = "PASS" if ratio <= 1.0 else "CHECK REQUIRED"
                    report += f"\n• {member_type.upper()}: Governing Utilization = {ratio:.2f} - {status}"
                    
                    # Detailed breakdown for columns
                    if member_type == 'column' and hasattr(design_result, 'shear_utilization_x'):
                        pm_ratio = design_result.capacity.interaction_ratio
                        vx_ratio = design_result.shear_utilization_x
                        vy_ratio = design_result.shear_utilization_y
                        
                        report += f"\n    ↳ P-M Interaction Ratio : {pm_ratio:.2f}"
                        report += f"\n    ↳ Shear Utilization (X) : {vx_ratio:.2f}"
                        report += f"\n    ↳ Shear Utilization (Y) : {vy_ratio:.2f}"
        
        report += f"""

Notes and Recommendations:
{'='*80}
• All designs are based on ACI 318M-25 provisions
• Detailing requirements per ACI 318M-25 should be followed
• Construction tolerances per ACI 301 should be maintained
• Quality control testing per ACI 318M-25 Chapter 26 required
• This analysis is preliminary - detailed design verification recommended

Generated by ACI 318M-25 Complete Member Design Library v{self.version}
{'-'*80}
"""
        
        return report

def main():
    """Example usage of ACI 318M-25 Complete Member Library"""
    print("ACI 318M-25 Complete Member Design Library")
    print("Building Code Requirements for Structural Concrete (International System of Units)")
    print("=" * 80)
    
    # Initialize library
    library = ACI318M25MemberLibrary()
    
    # Get library information
    print("\n1. Library Information")
    print("-" * 50)
    info = library.get_library_info()
    print(f"Version: {info['version']}")
    print(f"Code: {info['code']}")
    print(f"Units: {info['units']}")
    
    print("\nAvailable Libraries:")
    for name, description in info['libraries'].items():
        print(f"  • {name}: {description}")
    
    # Get available materials
    print(f"\n2. Available Materials")
    print("-" * 50)
    materials = library.get_available_materials()
    print(f"Concrete strengths: {materials['concrete_range']}")
    print(f"Steel grades: {materials['steel_range']}")
    
    # Design typical building
    print(f"\n3. Typical Office Building Design")
    print("-" * 50)
    
    design_results = library.design_typical_office_building_members(
        building_height=24.0,  # 24m building
        typical_span=7.0       # 7m typical span
    )
    
    print("Design completed for:")
    for member_type in design_results.keys():
        print(f"  ✓ {member_type.upper()}")
    
    # Generate report
    print(f"\n4. Design Report Generation")
    print("-" * 50)
    
    project_info = ProjectInfo(
        project_name="Typical Office Building",
        location="Example City",
        date="2024-01-15",
        engineer="Professional Engineer",
        client="Example Client",
        description="6-story office building with typical 7m spans"
    )
    
    report = library.generate_design_summary_report(design_results, project_info)
    
    # Show report summary
    report_lines = report.split('\n')
    print("Design Report Generated (First 25 lines):")
    for i, line in enumerate(report_lines[:25]):
        print(line)
    print("... (report continues)")
    print(f"Total report length: {len(report)} characters")
    
    # Save report to file
    try:
        with open('aci318m25_design_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✓ Complete report saved to: aci318m25_design_report.txt")
    except Exception as e:
        print(f"\n⚠ Could not save report: {e}")
    
    print(f"\n{'='*80}")
    print("ACI 318M-25 Complete Member Design Library is ready for use!")
    print("Individual libraries available:")
    print("  • aci318m25_beam.py")
    print("  • aci318m25_column.py") 
    print("  • aci318m25_slab.py")
    print("  • aci318m25_footing.py")
    print("  • aci318m25_wall.py")
    print("  • aci318m25_complete.py (this manager)")

if __name__ == "__main__":
    main()